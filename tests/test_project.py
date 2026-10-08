"""0.4.1 (#87): a project's files are found by name.

`Views/`, `ViewModels/`, `Components/`, `Themes/` and `Styles/` under the root are the standard places;
`search=` adds folders and `recursive=True` looks through the whole project. A name in two places is an error.
"""

import sys
import textwrap

import pytest

from tesserae import App
from tesserae.project import Project, ProjectError, is_name
from tesserae.spec import ViewWatcher

SEED = (0x67, 0x50, 0xA4, 0xFF)
VIEW = "id: root\nkind: Container\nchildren: []\n"


@pytest.fixture(autouse=True)
def _restore_imports():
    path, modules = list(sys.path), set(sys.modules)
    yield
    sys.path[:] = path
    for name in set(sys.modules) - modules:
        sys.modules.pop(name, None)


def _write(root, relative, text=""):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_a_name_is_not_a_path():
    assert is_name("Main") and is_name("My_Theme")
    assert not any(is_name(x) for x in ("Views/Main_View.yaml", "Main_View.yaml", "a\\b", "", None))


@pytest.mark.parametrize("kind, folder, suffix", [
    ("view", "Views", "_View.yaml"), ("viewmodel", "ViewModels", "_ViewModel.py"),
    ("component", "Components", "_Component.yaml"), ("theme", "Themes", "_Theme.yaml"),
    ("stylesheet", "Styles", "_Stylesheet.yaml"), ("style", "Styles", "_Style.yaml"),
])
def test_each_kind_is_found_in_its_standard_folder(tmp_path, kind, folder, suffix):
    file = _write(tmp_path, f"{folder}/Thing{suffix}")
    project = Project(tmp_path)
    assert project.find(kind, "Thing") == file
    assert project.index(kind) == {"Thing": file}


def test_a_file_in_the_wrong_folder_is_not_found(tmp_path):
    _write(tmp_path, "Themes/Main_View.yaml")
    with pytest.raises(ProjectError, match=r"no view called 'Main' \(Main_View.yaml\) in .*search=\["):
        Project(tmp_path).find("view", "Main")


def test_the_error_lists_the_folders_it_looked_in(tmp_path):
    (tmp_path / "Views").mkdir()
    with pytest.raises(ProjectError, match="in Views under"):
        Project(tmp_path).find("view", "Main")


def test_search_adds_folders_for_every_kind(tmp_path):
    other = _write(tmp_path, "shared/Thing_Theme.yaml")
    elsewhere = _write(tmp_path.parent / f"{tmp_path.name}_lib", "Out_View.yaml")
    project = Project(tmp_path, search=["shared", elsewhere.parent])
    assert project.find("theme", "Thing") == other
    assert project.find("view", "Out") == elsewhere


def test_recursive_searches_the_whole_project_and_not_what_isnt_its_own(tmp_path):
    deep = _write(tmp_path, "src/ui/screens/Deep_View.yaml")
    _write(tmp_path, ".venv/lib/Hidden_View.yaml")
    _write(tmp_path, "node_modules/x/Skipped_View.yaml")
    _write(tmp_path, "env/pyvenv.cfg")
    _write(tmp_path, "env/Env_View.yaml")
    assert Project(tmp_path, recursive=True).index("view") == {"Deep": deep}
    assert Project(tmp_path).index("view") == {}  # not unless asked


def test_a_name_in_two_places_is_an_error_naming_both(tmp_path):
    _write(tmp_path, "Views/Main_View.yaml")
    _write(tmp_path, "more/Main_View.yaml")
    with pytest.raises(ProjectError, match=r"Main_View.yaml is in two places, Views.Main_View.yaml and more.Main_View.yaml"):
        Project(tmp_path, search=["more"]).find("view", "Main")


def test_a_path_is_used_as_it_is_and_a_name_is_found(tmp_path):
    file = _write(tmp_path, "Themes/Brand_Theme.yaml")
    project = Project(tmp_path)
    assert project.resolve("theme", "Brand") == file
    assert project.resolve("theme", str(file)) == file
    assert project.resolve("theme", file) == file


def test_the_components_folders_are_the_ones_with_components(tmp_path):
    _write(tmp_path, "Components/A_Component.yaml")
    _write(tmp_path, "widgets/B_Component.yaml")
    (tmp_path / "Empty").mkdir()
    assert Project(tmp_path, search=["widgets", "Empty"]).component_dirs() == [tmp_path / "Components", tmp_path / "widgets"]


def test_a_viewmodel_is_imported_by_its_name_and_its_folder_is_on_the_path(tmp_path):
    _write(tmp_path, "ViewModels/Helper_ViewModel.py", "class HelperViewModel:\n    pass\n")
    _write(tmp_path, "ViewModels/Main_ViewModel.py",
           "from Helper_ViewModel import HelperViewModel\n\nclass MainViewModel(HelperViewModel):\n    pass\n")
    cls = Project(tmp_path).viewmodel("Main")
    assert cls.__name__ == "MainViewModel" and cls.__mro__[1].__name__ == "HelperViewModel"


def test_a_viewmodel_file_without_its_class_says_what_it_has(tmp_path):
    _write(tmp_path, "ViewModels/Main_ViewModel.py", "class OtherViewModel:\n    pass\n")
    with pytest.raises(ProjectError, match=r"Main_ViewModel.py has no class MainViewModel \(it has OtherViewModel\)"):
        Project(tmp_path).viewmodel("Main")


def test_a_second_project_with_the_same_viewmodel_name_is_refused_not_mixed_up(tmp_path):
    for folder in ("a", "b"):
        _write(tmp_path / folder, "ViewModels/Main_ViewModel.py", "class MainViewModel:\n    pass\n")
    Project(tmp_path / "a").viewmodel("Main")
    with pytest.raises(ProjectError, match="already imported from"):
        Project(tmp_path / "b").viewmodel("Main")


# -- in an app ---------------------------------------------------------------------------------

def _app_files(root):
    _write(root, "Views/Main_View.yaml", textwrap.dedent("""\
        id: root
        kind: Container
        style: row_Style.yaml
        children:
          - id: stat
            component: Stat
            with: {label: Open}
    """))
    _write(root, "ViewModels/Main_ViewModel.py", "from tesserae import ViewModel\n\nclass MainViewModel(ViewModel):\n    pass\n")
    _write(root, "Components/Stat_Component.yaml", textwrap.dedent("""\
        params: [label]
        id: root
        kind: Text
        text: {content: "{{ label }}", typography_role: body_large}
    """))
    _write(root, "Components/Stat_Stylesheet.yaml", "styles:\n  - {id: root, style: {foreground: tertiary}}\n")
    _write(root, "Styles/row_Style.yaml", "flex_direction: vertical\ngap: 7\n")
    _write(root, "Themes/Brand_Theme.yaml", 'seed: "#0B6B58"\n')
    _write(root, "Styles/Page_Stylesheet.yaml", "styles:\n  - {classes: [page], style: {padding: 9}}\n")


def test_load_finds_the_view_and_its_viewmodel_by_name(tmp_path):
    _app_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    view, viewmodel = app.load("Main")
    assert type(viewmodel).__name__ == "MainViewModel" and app.current is None
    assert view.node("root").get("gap") == 7.0  # `style: row_Style.yaml`, found in Styles/
    assert view.node("stat").get("text") == "Open"  # `component: Stat`, found in Components/


def test_a_component_in_the_project_has_its_stylesheet(tmp_path):
    _app_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path, theme_seed=SEED)
    view, _ = app.load("Main")
    assert view.spec["children"][0]["style"] == {"foreground": "tertiary"}


def test_themes_and_stylesheets_are_found_by_name(tmp_path):
    _app_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path, custom_theme="Brand", stylesheet="Page")
    assert app._custom_theme_spec == {"seed": "#0B6B58"}
    assert app._stylesheet_spec == {"styles": [{"classes": ["page"], "style": {"padding": 9}}]}
    assert app._theme_files["custom"] == tmp_path / "Themes" / "Brand_Theme.yaml"  # hot reload watches the file


def test_a_view_given_as_a_path_still_works_and_finds_its_viewmodel_in_the_project(tmp_path):
    _app_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    _, viewmodel = app.load(tmp_path / "Views" / "Main_View.yaml")
    assert type(viewmodel).__name__ == "MainViewModel"


def test_a_viewmodel_beside_the_view_is_used_before_the_projects(tmp_path):
    _write(tmp_path, "Beside_View.yaml", VIEW)
    _write(tmp_path, "Beside_ViewModel.py", "from tesserae import ViewModel\n\nclass BesideViewModel(ViewModel):\n    pass\n")
    app = App(width=300, height=200, root=tmp_path / "elsewhere")
    _, viewmodel = app.load(tmp_path / "Beside_View.yaml")
    assert type(viewmodel).__name__ == "BesideViewModel"


def test_an_unknown_name_says_where_it_looked(tmp_path):
    app = App(width=300, height=200, root=tmp_path)
    with pytest.raises(ProjectError, match="no view called 'Nope'"):
        app.load("Nope")


def test_search_and_recursive_reach_an_app(tmp_path):
    _write(tmp_path, "screens/Far_View.yaml", VIEW)
    _write(tmp_path, "screens/Far_ViewModel.py", "from tesserae import ViewModel\n\nclass FarViewModel(ViewModel):\n    pass\n")
    assert App(width=300, height=200, root=tmp_path, search=["screens"]).load("Far")[1] is not None
    assert App(width=300, height=200, root=tmp_path, recursive=True).project.recursive


def test_two_components_with_one_name_stop_the_view_that_uses_them(tmp_path):
    _app_files(tmp_path)
    _write(tmp_path, "more/Stat_Component.yaml", "id: root\nkind: Text\n")
    app = App(width=300, height=200, root=tmp_path, search=["more"])
    with pytest.raises(ProjectError, match="Stat_Component.yaml is in two places"):
        app.load("Main")


def test_hot_reload_watches_the_projects_components_and_styles(tmp_path):
    _app_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    view, _ = app.load("Main")
    watched = ViewWatcher(view, view.path, project=app.project).files
    assert {p.name for p in watched} >= {"Main_View.yaml", "Stat_Component.yaml", "Stat_Stylesheet.yaml", "row_Style.yaml"}


def test_a_view_built_outside_an_app_does_not_search_a_project():
    spec = {"id": "r", "kind": "Container", "children": [{"id": "c", "component": "NoSuch"}]}
    from tesserae.spec import expand_components_to_spec
    from tesserae.spec.expand import ComponentError

    with pytest.raises(ComponentError, match="unknown component 'NoSuch'"):
        expand_components_to_spec(__import__("yaml").safe_dump(spec))


# -- Repeater and instantiate use the same names (#89) --------------------------------------

def _list_files(root):
    _write(root, "Views/List_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: rows, kind: Container}\n")
    _write(root, "ViewModels/List_ViewModel.py", "from tesserae import ViewModel\n\nclass ListViewModel(ViewModel):\n    pass\n")
    _write(root, "Views/Row_View.yaml", "id: root\nkind: Text\ntext: {content: row, typography_role: body_large}\nstyle: {foreground: on_surface}\n")
    _write(root, "ViewModels/Row_ViewModel.py",
           "from tesserae import ViewModel\n\nclass RowViewModel(ViewModel):\n    def __init__(self, view, item):\n"
           "        self.item = item\n        super().__init__(view)\n")


def test_a_repeater_takes_a_view_name_and_finds_its_viewmodel(tmp_path):
    from tesserae import Repeater, Signal

    _list_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    view, _ = app.load("List")
    items = Signal([1, 2])
    rows = Repeater(view, items, "Row", into=view.node("rows"))  # no path, no class
    assert [vm.item for _, _, vm in rows] == [1, 2]
    items.set([1, 2, 3])
    assert len(rows) == 3
    assert {c.path.name for _, c, _ in rows} == {"Row_View.yaml"}


def test_a_repeater_still_takes_a_path_and_a_class(tmp_path):
    from tesserae import Repeater, Signal

    _list_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    view, _ = app.load("List")
    cls = app.project.viewmodel("Row")
    rows = Repeater(view, Signal([7]), tmp_path / "Views" / "Row_View.yaml", cls, view.node("rows"))
    assert [vm.item for _, _, vm in rows] == [7]


def test_instantiate_takes_a_name_and_finds_its_viewmodel(tmp_path):
    from tesserae import instantiate

    _list_files(tmp_path)
    app = App(width=300, height=200, root=tmp_path)
    view, _ = app.load("List")
    component, viewmodel = instantiate(view, "Row", into=view.node("rows"), item=5)
    assert type(viewmodel).__name__ == "RowViewModel" and viewmodel.item == 5 and component.path.name == "Row_View.yaml"


def test_a_name_with_no_app_is_an_error_that_says_there_is_no_project():
    from tesserae import Repeater, Signal, View

    view = View({"id": "root", "kind": "Container", "children": [{"id": "rows", "kind": "Container"}]}, theme_seed=SEED)
    with pytest.raises(ProjectError, match="'Row' is a name, but there is no project to look in"):
        Repeater(view, Signal([]), "Row", into=view.node("rows"))


def test_into_is_required():
    from tesserae import Repeater, Signal, View, instantiate

    view = View({"id": "root", "kind": "Container"}, theme_seed=SEED)
    with pytest.raises(TypeError, match="needs `into`"):
        Repeater(view, Signal([]), "x_View.yaml")
    with pytest.raises(TypeError, match="needs `into`"):
        instantiate(view, "x_View.yaml")
