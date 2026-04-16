import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { fetchAdminMenuTree } from "../../services/adminMenuApi";
import { adminService } from "../../services/adminService";
import { useAuthStore } from "../../store/useAuthStore";
import type {
  AdminGroupMenuPermissionResponse,
  AdminMenu,
  AdminMenuTreeResponse,
} from "../../types/admin";
import { buildMenuTree } from "../../utils/buildMenuTree";

interface AdminSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

function createFallbackMenuTree() {
  return buildMenuTree(adminService.getAdminMenus().filter((menu) => menu.useTf === "Y"));
}

function sortTree(nodes: AdminMenuTreeResponse[]) {
  return [...nodes]
    .sort((left, right) => {
      if (left.sortNo !== right.sortNo) {
        return left.sortNo - right.sortNo;
      }

      return left.id - right.id;
    })
    .map((node) => ({
      ...node,
      children: sortTree(node.children ?? []),
    }));
}

function normalizeTreeNode(node: AdminMenuTreeResponse): AdminMenuTreeResponse {
  return {
    ...node,
    parentId: node.parentId ?? null,
    menuPath: node.menuPath ?? null,
    icon: node.icon ?? null,
    children: (node.children ?? []).map(normalizeTreeNode),
  };
}

function filterMenuTreeByPermissions(
  menuTree: AdminMenuTreeResponse[],
  permissions: AdminGroupMenuPermissionResponse[],
) {
  if (permissions.length === 0) {
    return sortTree(menuTree);
  }

  const readableMenuIds = new Set(
    permissions
      .filter((permission) => permission.readTf === "Y" && permission.useTf !== "N")
      .map((permission) => permission.menuId),
  );

  const visit = (node: AdminMenuTreeResponse): AdminMenuTreeResponse | null => {
    const filteredChildren = (node.children ?? [])
      .map(visit)
      .filter((child): child is AdminMenuTreeResponse => Boolean(child));

    if (readableMenuIds.has(node.id) || filteredChildren.length > 0) {
      return {
        ...node,
        children: sortTree(filteredChildren),
      };
    }

    return null;
  };

  return sortTree(
    menuTree
      .map(visit)
      .filter((node): node is AdminMenuTreeResponse => Boolean(node)),
  );
}

function isPathActive(menuPath: string | null, pathname: string) {
  if (!menuPath) {
    return false;
  }

  return pathname === menuPath || pathname.startsWith(`${menuPath}/`);
}

export function AdminSidebar({ isOpen, onClose }: AdminSidebarProps) {
  const location = useLocation();
  const admin = useAuthStore((state) => state.admin);
  const permissions = useAuthStore((state) => state.permissions);
  const [openParentId, setOpenParentId] = useState<number | null>(null);
  const [menuTreeSource, setMenuTreeSource] = useState<AdminMenuTreeResponse[]>(
    createFallbackMenuTree(),
  );

  useEffect(() => {
    let isMounted = true;

    const loadMenuTree = async () => {
      try {
        const data = await fetchAdminMenuTree("Y");
        if (!isMounted) {
          return;
        }

        setMenuTreeSource(sortTree(data.map(normalizeTreeNode)));
      } catch (error) {
        console.error("사이드바 메뉴 트리 로드 실패:", error);
        if (!isMounted) {
          return;
        }

        setMenuTreeSource(createFallbackMenuTree());
      }
    };

    void loadMenuTree();

    return () => {
      isMounted = false;
    };
  }, []);

  const menuTree = useMemo(
    () => filterMenuTreeByPermissions(menuTreeSource, permissions),
    [menuTreeSource, permissions],
  );

  useEffect(() => {
    const matchedChild = menuTree
      .flatMap((menu) => menu.children.map((child) => ({ parentId: menu.id, child })))
      .find(({ child }) => isPathActive(child.menuPath, location.pathname));

    if (matchedChild) {
      setOpenParentId(matchedChild.parentId);
      return;
    }

    const matchedParent = menuTree.find((menu) => isPathActive(menu.menuPath, location.pathname));
    if (matchedParent) {
      setOpenParentId(matchedParent.id);
    }
  }, [location.pathname, menuTree]);

  return (
    <>
      <aside className={`admin-sidebar ${isOpen ? "is-open" : ""}`}>
        <div className="admin-sidebar__brand">
          <div className="brand-mark">HR</div>
          <div>
            <p>HR Copilot</p>
            <span>Admin Workspace</span>
          </div>
        </div>

        <div className="admin-sidebar__section">
          <p className="admin-sidebar__label">관리 메뉴</p>
          <nav className="admin-sidebar__nav admin-sidebar__nav--tree">
            {menuTree.map((menu) => {
              const hasChildren = menu.children.length > 0;
              const isOpenSection = openParentId === menu.id;
              const isParentActive = isPathActive(menu.menuPath, location.pathname);

              return (
                <div key={menu.id} className="admin-sidebar__group">
                  {hasChildren ? (
                    <button
                      type="button"
                      className={`admin-sidebar__parent ${isOpenSection || isParentActive ? "is-active" : ""}`}
                      onClick={() =>
                        setOpenParentId((current) => (current === menu.id ? null : menu.id))
                      }
                    >
                      {menu.menuName}
                    </button>
                  ) : (
                    <NavLink
                      to={menu.menuPath || "#"}
                      onClick={() => {
                        if (window.innerWidth < 768) {
                          onClose();
                        }
                      }}
                      className={({ isActive }) =>
                        `admin-sidebar__parent ${isActive ? "is-active" : ""}`
                      }
                    >
                      {menu.menuName}
                    </NavLink>
                  )}

                  {hasChildren && isOpenSection ? (
                    <div className="admin-sidebar__children">
                      {menu.children.map((child) => (
                        <NavLink
                          key={child.id}
                          to={child.menuPath || "#"}
                          onClick={() => {
                            if (window.innerWidth < 768) {
                              onClose();
                            }
                          }}
                          className={({ isActive }) =>
                            `admin-sidebar__child ${isActive ? "is-active" : ""}`
                          }
                        >
                          ㄴ {child.menuName}
                        </NavLink>
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </nav>
        </div>

        <div className="admin-sidebar__footer">
          <p className="admin-sidebar__label">관리자 정보</p>
          <div className="sidebar-note">
            <strong>{admin?.name ?? "운영 관리자"}</strong>
            <span>{admin?.email ?? "admin@hrcopilot.ai"}</span>
          </div>
        </div>
      </aside>

      {isOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={onClose}
          aria-label="사이드바 닫기"
        />
      ) : null}
    </>
  );
}
