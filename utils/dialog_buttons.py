class DialogButtons:
    """A class that contains constants."""

    ok: str = "Ok"
    yes: str = "Yes"
    no: str = "No"
    cancel: str = "Cancel"
    copy: str = "Copy"
    save: str = "Save"
    clone: str = "Clone"
    add: str = "Add"
    delete: str = "Delete"
    discard: str = "Discard"
    update: str = "Update"
    open: str = "Open"
    ok_cancel: str = ", ".join([ok, cancel])
    no_yes_cancel: str = ", ".join([no, yes, cancel])
    delete_cancel: str = ", ".join([delete, cancel])
    discard_cancel: str = ", ".join([discard, cancel])
    clone_cancel: str = ", ".join([clone, cancel])
    add_cancel: str = ", ".join([add, cancel])
    yes_no_cancel: str = ", ".join([yes, no, cancel])
    save_cancel: str = ", ".join([save, cancel])
    open_cancel: str = ", ".join([open, cancel])
    ok_update: str = ", ".join([ok, update])
    ok_copy_cancel: str = ", ".join([ok, copy, cancel])
    ok_save_copy_cancel: str = ", ".join([ok, save, copy, cancel])
