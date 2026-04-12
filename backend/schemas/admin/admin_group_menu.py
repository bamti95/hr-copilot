from pydantic import BaseModel, ConfigDict, Field


class AdminGroupMenuPermissionRequest(BaseModel):
    menu_id: int = Field(..., alias="menuId")
    read_tf: str = Field(default="Y", alias="readTf", pattern="^(Y|N)$")
    write_tf: str = Field(default="N", alias="writeTf", pattern="^(Y|N)$")
    delete_tf: str = Field(default="N", alias="deleteTf", pattern="^(Y|N)$")
    use_tf: str = Field(default="Y", alias="useTf", pattern="^(Y|N)$")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class AdminGroupMenuPermissionResponse(BaseModel):
    id: int
    menu_id: int = Field(..., alias="menuId")
    parent_id: int | None = Field(None, alias="parentId")
    menu_name: str = Field(..., alias="menuName")
    menu_key: str = Field(..., alias="menuKey")
    menu_path: str | None = Field(None, alias="menuPath")
    depth: int
    sort_no: int = Field(..., alias="sortNo")
    icon: str | None = None
    read_tf: str = Field(..., alias="readTf")
    write_tf: str = Field(..., alias="writeTf")
    delete_tf: str = Field(..., alias="deleteTf")
    use_tf: str = Field(..., alias="useTf")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def from_entities(group_menu, menu) -> "AdminGroupMenuPermissionResponse":
        return AdminGroupMenuPermissionResponse(
            id=group_menu.id,
            menuId=menu.id,
            parentId=menu.parent_id,
            menuName=menu.menu_name,
            menuKey=menu.menu_key,
            menuPath=menu.menu_path,
            depth=menu.depth,
            sortNo=menu.sort_no,
            icon=menu.icon,
            readTf=group_menu.read_tf,
            writeTf=group_menu.write_tf,
            deleteTf=group_menu.delete_tf,
            useTf=group_menu.use_tf,
        )
