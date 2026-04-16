import type { AdminGroupMenuPermissionRequest, AdminMenuTreeResponse } from "../../../../types/admin";
import { flattenMenuTree } from "../../../../utils/menuTreeFlattener";

interface AdminGroupPermissionTableProps {
  menus: AdminMenuTreeResponse[];
  permissions: AdminGroupMenuPermissionRequest[];
  disabled?: boolean;
  title?: string;
  description?: string;
  onChange: (
    menuId: number,
    field: "readTf" | "writeTf" | "deleteTf" | "useTf",
    checked: boolean,
  ) => void;
}

export function AdminGroupPermissionTable({
  menus,
  permissions,
  disabled = false,
  title = "메뉴 권한",
  description,
  onChange,
}: AdminGroupPermissionTableProps) {
  const flattenedMenus = flattenMenuTree(menus);
  const permissionMap = new Map(permissions.map((item) => [item.menuId, item]));

  return (
    <div className="permission-panel">
      <div className="permission-panel__header">
        <div>
          <strong>{title}</strong>
          {description ? <span>{description}</span> : null}
        </div>
        <span>{flattenedMenus.length}개 메뉴</span>
      </div>
      <div className="permission-table">
        {flattenedMenus.map((menu) => {
          const permission = permissionMap.get(menu.id);

          return (
            <div key={menu.id} className="permission-table__row">
              <div className="permission-table__menu" style={{ paddingLeft: `${menu.level * 18}px` }}>
                {menu.level > 0 ? "└ " : ""}
                {menu.menuName}
              </div>
              <label><input type="checkbox" disabled={disabled} checked={permission?.readTf === "Y"} onChange={(event) => onChange(menu.id, "readTf", event.target.checked)} />읽기</label>
              <label><input type="checkbox" disabled={disabled} checked={permission?.writeTf === "Y"} onChange={(event) => onChange(menu.id, "writeTf", event.target.checked)} />쓰기</label>
              <label><input type="checkbox" disabled={disabled} checked={permission?.deleteTf === "Y"} onChange={(event) => onChange(menu.id, "deleteTf", event.target.checked)} />삭제</label>
              <label><input type="checkbox" disabled={disabled} checked={permission?.useTf !== "N"} onChange={(event) => onChange(menu.id, "useTf", event.target.checked)} />사용</label>
            </div>
          );
        })}
      </div>
    </div>
  );
}
