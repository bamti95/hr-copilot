import type { AdminMenu } from "../types/admin";

export function buildAdminMenuTree(menus: AdminMenu[]) {
  const ordered = [...menus].sort((a, b) => a.sortNo - b.sortNo);

  return ordered
    .filter((menu) => menu.parentId === null)
    .map((menu) => ({
      ...menu,
      children: ordered.filter((child) => child.parentId === menu.id),
    }));
}
