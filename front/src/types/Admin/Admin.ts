export interface Admin {
  id: number;
  loginId?: string;
  name: string;
  email: string;
  groupId: number;
  isDeleted: boolean;
}
