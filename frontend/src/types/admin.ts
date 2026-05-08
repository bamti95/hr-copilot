export interface AdminMenu {
  id: number;
  parentId: number | null;
  sortNo: number;
  name?: string;
  label?: string;
  path?: string;
  [key: string]: unknown;
}
