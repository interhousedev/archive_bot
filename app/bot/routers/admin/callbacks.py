from aiogram.filters.callback_data import CallbackData


class CreateCancel(CallbackData, prefix="cr_cancel"):
    pass


class CreateSkipDescription(CallbackData, prefix="cr_skip"):
    pass


class ManageBack(CallbackData, prefix="mg_back"):
    pass


class ManageSelectEvent(CallbackData, prefix="mg_ev"):
    event_id: str


class ManageEditField(CallbackData, prefix="mg_ef"):
    event_id: str
    field: str  # "name" | "date" | "description"


class ManageDelete(CallbackData, prefix="mg_del"):
    event_id: str


class ManageDeleteConfirm(CallbackData, prefix="mg_dc"):
    event_id: str


class ManageEventFiles(CallbackData, prefix="mg_evf"):
    event_id: str
    page: int = 0


class ManageFileDetail(CallbackData, prefix="mg_fdt"):
    file_id: str
    page: int


class ManageFileToggleBan(CallbackData, prefix="mg_ftb"):
    file_id: str
    page: int


class ManageFileDelete(CallbackData, prefix="mg_fd"):
    file_id: str
    page: int


class ManageFileDeleteConfirm(CallbackData, prefix="mg_fdc"):
    file_id: str
    page: int


class AdminBanFile(CallbackData, prefix="adm_bf"):
    file_id: str
    author_telegram_id: int


class AdminUnbanFile(CallbackData, prefix="adm_ubf"):
    file_id: str
    author_telegram_id: int


class AdminToggleSender(CallbackData, prefix="adm_ts"):
    file_id: str
    author_telegram_id: int


class AdminNoop(CallbackData, prefix="adm_np"):
    pass