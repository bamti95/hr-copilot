import { useMemo } from "react";
import { useAuthStore } from "../store/useAuthStore";

export function useAdminPermission(menuKey: string) {
  const permissions = useAuthStore((state) => state.permissions);

  return useMemo(() => {
    const matched = permissions.find((permission) => permission.menuKey === menuKey);

    if (!matched) {
      return {
        canRead: true,
        canWrite: true,
        canDelete: true,
        canUse: true,
      };
    }

    return {
      canRead: matched.readTf === "Y",
      canWrite: matched.writeTf === "Y",
      canDelete: matched.deleteTf === "Y",
      canUse: matched.useTf === "Y",
    };
  }, [menuKey, permissions]);
}
