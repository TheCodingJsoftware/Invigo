import qtawesome as qta

# qta-browser to view icons
from ui.theme import theme_var
from utils.colors import get_on_color_from_primary


def make_icon(name: str, theme: str):
    return qta.icon(
        name,
        color_on=theme_var(theme),
        color_on_active=theme_var(theme),
        color_off=get_on_color_from_primary(theme_var(theme)),
        color_off_active=get_on_color_from_primary(theme_var(theme)),
    )


class Icons:
    invigo_icon = "icons/icon.png"
    refresh_icon = None
    clear_icon = None
    save_icon = None
    save_as_icon = None
    import_icon = None
    calendar_icon = None
    workspace_icon = None
    graph_icon = None
    quit_icon = None
    edit_user_icon = None
    edit_icon = None
    font_icon = None
    edit_workspace_settings_icon = None
    sort_icon = None
    add_file_icon = None
    remove_file_icon = None
    open_folder_icon = None
    add_folder_icon = None
    remove_folder_icon = None
    generate_file_icon = None
    website_icon = None
    open_window_icon = None
    action_history_icon = None
    button_history_icon = None
    info_icon = None
    question_icon = None
    update_icon = None
    maximized_icon = None
    inventory_icon = None
    sheet_settings_icon = None
    calculator_icon = None
    job_planner_icon = None
    action_workspace_icon = None
    paint_icon = None
    plus_icon = None
    plus_circle_icon = None
    minus_icon = None
    dock_icon = None
    redock_icon = None
    delete_icon = None
    eye_icon = None
    copy_icon = None
    filter_icon = None
    sort_fill_icon = None
    date_range_icon = None
    folder_icon = None
    sun_icon = None
    moon_icon = None
    flowtag_data_icon = None
    printer_icon = None
    check_fill_icon = None
    arrow_right_fill_icon = None
    recut_icon = None
    recoat_icon = None
    merge_icon = None
    job_planning_icon = None
    job_quoting_icon = None
    job_quoted_icon = None
    job_quote_confirmed_icon = None
    job_template_icon = None
    job_workspace_icon = None
    job_archive_icon = None

    @classmethod
    def load_icons(cls):
        cls.refresh_icon = qta.icon(
            "ph.arrows-clockwise",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.clear_icon = qta.icon(
            "ph.x",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.save_icon = qta.icon(
            "ri.save-2-fill",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.save_as_icon = qta.icon(
            "ri.save-3-fill",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.import_icon = qta.icon(
            "ri.file-download-fill",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.calendar_icon = qta.icon(
            "ph.calendar-check-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.workspace_icon = qta.icon(
            "fa6s.network-wired",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )

        # QAction Icons
        cls.graph_icon = qta.icon(
            "msc.graph-line",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.quit_icon = qta.icon(
            "ph.x-square-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.edit_user_icon = qta.icon(
            "ph.user-circle-gear-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.edit_icon = qta.icon(
            "ph.pencil-simple-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.font_icon = qta.icon(
            "ph.text-aa-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.edit_workspace_settings_icon = qta.icon(
            "ph.faders-horizontal-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.sort_icon = qta.icon(
            "ph.funnel-simple-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.add_file_icon = qta.icon(
            "ph.file-plus-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.remove_icon = qta.icon(
            "msc.remove",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.remove_file_icon = qta.icon(
            "ph.file-x-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.open_folder_icon = qta.icon(
            "ph.folder-open-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.add_folder_icon = qta.icon(
            "ph.folder-simple-plus-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.remove_folder_icon = qta.icon(
            "ph.folder-simple-minus-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.generate_file_icon = qta.icon(
            "ph.file-dotted-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.website_icon = qta.icon(
            "ph.globe",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.open_window_icon = qta.icon(
            "ph.app-window-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.action_history_icon = qta.icon(
            "ph.clock-counter-clockwise",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.button_history_icon = qta.icon(
            "ph.clock-counter-clockwise",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.info_icon = qta.icon(
            "ph.info-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.question_icon = qta.icon(
            "ph.question-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.update_icon = qta.icon(
            "ph.clock-clockwise",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.maximized_icon = qta.icon(
            "ph.frame-corners-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.inventory_icon = qta.icon(
            "ph.package-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.sheet_settings_icon = qta.icon(
            "ri.list-settings-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.calculator_icon = qta.icon(
            "ph.calculator-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.job_planner_icon = qta.icon(
            "ph.calendar-blank-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.action_workspace_icon = qta.icon(
            "fa6s.network-wired",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.paint_icon = qta.icon(
            "ph.palette-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.paint_brush_icon = qta.icon(
            "ph.paint-brush-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.plus_icon = qta.icon(
            "ph.plus",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.plus_circle_icon = qta.icon(
            "ph.plus-circle-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.minus_icon = qta.icon(
            "ph.minus",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.dock_icon = qta.icon(
            "ph.arrows-out-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.redock_icon = qta.icon(
            "ph.arrows-in-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.delete_icon = qta.icon(
            "ph.trash-fill",
            color_on=theme_var("on-primary-red"),
            color_on_active=theme_var("on-primary-red"),
            color_off=theme_var("on-primary-red"),
            color_off_active=theme_var("on-primary-red"),
        )
        cls.eye_icon = qta.icon(
            "ph.eye-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )

        cls.copy_icon = qta.icon(
            "ph.copy-simple-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.filter_icon = qta.icon(
            "ph.funnel-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.sort_fill_icon = qta.icon(
            "ph.funnel-simple-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.date_range_icon = qta.icon(
            "ph.calendar-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.folder_icon = qta.icon(
            "ph.folder-fill",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.sun_icon = qta.icon(
            "ph.sun-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.moon_icon = qta.icon(
            "ph.moon-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.flowtag_data_icon = qta.icon(
            "ph.sliders-horizontal-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.printer_icon = qta.icon(
            "ph.printer-fill",
            color_on=theme_var("on-surface"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("on-surface"),
            color_off_active=theme_var("primary"),
        )
        cls.check_fill_icon = qta.icon(
            "ph.check-circle-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.arrow_right_fill_icon = qta.icon(
            "ph.arrow-fat-line-right-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.recut_icon = qta.icon(
            "ph.arrow-u-down-left-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.recoat_icon = qta.icon(
            "ph.arrow-u-down-left-fill",
            color_on=theme_var("on-primary"),
            color_on_active=theme_var("on-primary"),
            color_off=theme_var("on-primary"),
            color_off_active=theme_var("on-primary"),
        )
        cls.merge_icon = qta.icon(
            "ph.git-merge-fill",
            color_on=theme_var("primary"),
            color_on_active=theme_var("primary"),
            color_off=theme_var("primary"),
            color_off_active=theme_var("primary"),
        )
        cls.job_planning_icon = make_icon("fa6s.calendar", "job-planning")
        cls.job_quoting_icon = make_icon("fa6s.file-invoice-dollar", "job-quoting")
        cls.job_quoted_icon = make_icon("ph.check-fill", "job-quoted")
        cls.job_quote_confirmed_icon = make_icon("ph.checks-fill", "job-quote-confirmed")
        cls.job_template_icon = make_icon("fa6s.box-archive", "job-template")
        cls.job_workspace_icon = make_icon("fa6s.network-wired", "job-workspace")
        cls.job_archive_icon = make_icon("fa6s.box-archive", "job-archive")
