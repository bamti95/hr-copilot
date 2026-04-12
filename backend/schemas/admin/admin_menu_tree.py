from pydantic import BaseModel, Field, ConfigDict

class AdmMenuTreeResponse(BaseModel):
    id: int
    parent_id: int | None = Field(None, alias="parentId")
    menu_name: str = Field(..., alias="menuName")
    menu_key: str = Field(..., alias="menuKey")
    menu_path: str | None = Field(None, alias="menuPath")
    depth: int
    sort_no: int = Field(..., alias="sortNo")
    icon: str | None = None
    use_tf: str | None = Field(None, alias="useTf")
    children: list["AdmMenuTreeResponse"] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @staticmethod
    def from_entity(entity, children: list["AdmMenuTreeResponse"] | None = None) -> "AdmMenuTreeResponse":
        return AdmMenuTreeResponse(
            id=entity.id,
            parentId=entity.parent_id,
            menuName=entity.menu_name,
            menuKey=entity.menu_key,
            menuPath=entity.menu_path,
            depth=entity.depth,
            sortNo=entity.sort_no,
            icon=entity.icon,
            useTf=entity.use_tf,
            children=children or [],
        )


AdmMenuTreeResponse.model_rebuild()
