import qtawesome as qta

from ui.theme import theme_var


class Icons:
    invigo_icon = "icons/invigo.png"
    refresh_icon = None
    clear_icon = None
    save_icon = None
    save_as_icon = None
    import_icon = None
    calendar_icon = None
    workspace_icon = None
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
    history_icon = None
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

    @classmethod
    def load_icons(cls):
        cls.refresh_icon = qta.icon(
            "ph.arrows-clockwise",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.clear_icon = qta.icon(
            "ph.x",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.save_icon = qta.icon(
            "ri.save-2-fill",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.save_as_icon = qta.icon(
            "ri.save-3-fill",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.import_icon = qta.icon(
            "ri.file-download-fill",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.calendar_icon = qta.icon(
            "ph.calendar-check-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )

        cls.workspace_icon = qta.icon(
            "ph.users-three-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )

        # QAction Icons
        cls.quit_icon = qta.icon(
            "ph.x-square-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.edit_user_icon = qta.icon(
            "ph.user-circle-gear-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.edit_icon = qta.icon(
            "ph.pencil-simple-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.font_icon = qta.icon(
            "ph.text-aa-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.edit_workspace_settings_icon = qta.icon(
            "ph.faders-horizontal-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.sort_icon = qta.icon(
            "ph.funnel-simple-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.add_file_icon = qta.icon(
            "ph.file-plus-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.remove_file_icon = qta.icon(
            "ph.file-x-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.open_folder_icon = qta.icon(
            "ph.folder-open-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.add_folder_icon = qta.icon(
            "ph.folder-simple-plus-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.remove_folder_icon = qta.icon(
            "ph.folder-simple-minus-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.generate_file_icon = qta.icon(
            "ph.file-dotted-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.website_icon = qta.icon(
            "ph.globe",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.open_window_icon = qta.icon(
            "ph.app-window-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.history_icon = qta.icon(
            "ph.clock-counter-clockwise",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.info_icon = qta.icon(
            "ph.info-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.question_icon = qta.icon(
            "ph.question-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.update_icon = qta.icon(
            "ph.clock-clockwise",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.maximized_icon = qta.icon(
            "ph.frame-corners-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.inventory_icon = qta.icon(
            "ph.package-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.sheet_settings_icon = qta.icon(
            "ri.list-settings-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.calculator_icon = qta.icon(
            "ph.calculator-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.job_planner_icon = qta.icon(
            "ph.calendar-blank-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.action_workspace_icon = qta.icon(
            "ph.users-three-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.paint_icon = qta.icon(
            "ph.palette-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.paint_brush_icon = qta.icon(
            "ph.paint-brush-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.plus_icon = qta.icon(
            "ph.plus",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.plus_circle_icon = qta.icon(
            "ph.plus-circle-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )
        cls.minus_icon = qta.icon(
            "ph.minus",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.dock_icon = qta.icon(
            "ph.arrows-out-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.redock_icon = qta.icon(
            "ph.arrows-in-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.delete_icon = qta.icon(
            "ph.trash-fill",
            options=[
                {
                    "color": theme_var("on-primary-red"),
                    "color_active": theme_var("on-primary-red"),
                    "color_selected": theme_var("on-primary-red"),
                }
            ],
        )
        cls.eye_icon = qta.icon(
            "ph.eye-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )

        cls.copy_icon = qta.icon(
            "ph.copy-simple-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.filter_icon = qta.icon(
            "ph.funnel-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )
        cls.sort_fill_icon = qta.icon(
            "ph.funnel-simple-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )
        cls.date_range_icon = qta.icon(
            "ph.calendar-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )
        cls.folder_icon = qta.icon(
            "ph.folder-fill",
            options=[
                {
                    "color": theme_var("primary"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
        cls.sun_icon = qta.icon(
            "ph.sun-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.moon_icon = qta.icon(
            "ph.moon-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                    "color_selected": theme_var("on-primary"),
                }
            ],
        )
        cls.flowtag_data_icon = qta.icon(
            "ph.sliders-horizontal-fill",
            options=[
                {
                    "color": theme_var("on-primary"),
                    "color_active": theme_var("on-primary"),
                }
            ],
        )
        cls.printer_icon = qta.icon(
            "ph.printer-fill",
            options=[
                {
                    "color": theme_var("on-surface"),
                    "color_active": theme_var("primary"),
                }
            ],
        )
