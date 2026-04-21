export type FlattenedMenuOption<T> = T & {
  level: number;
  label: string;
};

export function flattenMenuTree<
  T extends { id: number; menuName: string; children?: T[] },
>(
  nodes: T[],
  level = 0,
  result: FlattenedMenuOption<T>[] = [],
): FlattenedMenuOption<T>[] {
  nodes.forEach((node) => {
    result.push({
      ...node,
      level,
      label: `${"  ".repeat(level)}${level > 0 ? "└ " : ""}${node.menuName}`,
    });

    if (node.children?.length) {
      flattenMenuTree(node.children, level + 1, result);
    }
  });

  return result;
}
