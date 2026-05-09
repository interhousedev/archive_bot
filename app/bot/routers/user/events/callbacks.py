from aiogram.filters.callback_data import CallbackData


class SelectEvent(CallbackData, prefix="sel_ev"):
    event_id: str


class StartUpload(CallbackData, prefix="st_upl"):
    event_id: str


class ListMyFiles(CallbackData, prefix="lst_mf"):
    event_id: str


class FileAction(CallbackData, prefix="f_act"):
    file_id: str


class ToggleFile(CallbackData, prefix="tgl_f"):
    file_id: str