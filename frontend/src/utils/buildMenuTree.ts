import type { AdminMenu } from "../types/admin";

export type AdminMenuTreeNode = AdminMenu & {
  children: AdminMenuTreeNode[];
};

export function buildMenuTree(menus: AdminMenu[]): AdminMenuTreeNode[] {
  const nodeMap = new Map<number, AdminMenuTreeNode>();
  const roots: AdminMenuTreeNode[] = [];

  menus.forEach((menu) => {
    nodeMap.set(menu.id, { ...menu, children: [] });
  });

  menus.forEach((menu) => {
    const currentNode = nodeMap.get(menu.id);

    if (!currentNode) {
      return;
    }

    if (menu.parentId === null) {
      roots.push(currentNode);
      return;
    }

    const parentNode = nodeMap.get(menu.parentId);
    parentNode?.children.push(currentNode);
  });

  const sortRecursive = (nodes: AdminMenuTreeNode[]) => {
    nodes.sort((left, right) => left.sortNo - right.sortNo);
    nodes.forEach((node) => sortRecursive(node.children));
  };

  sortRecursive(roots);

  return roots;
}
