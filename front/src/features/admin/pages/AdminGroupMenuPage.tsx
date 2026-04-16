import { useEffect, useState } from "react";
import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { AdminGroupPermissionTable } from "../../admin/AdminGroup/components/AdminGroupPermissionTable.tsx";
import { useAdminPermission } from "../../../hooks/useAdminPermission";
import {
  fetchAdminGroupDetail,
  fetchAdminGroupList,
  updateAdminGroup,
} from "../../../services/adminGroupService";
import { fetchAdminMenuTree } from "../../../services/adminMenuApi";
import type {
  AdminGroupRequest,
  AdminGroupResponse,
  AdminMenuTreeResponse,
} from "../../../types/admin";
import { getErrorMessage } from "../../../utils/getErrorMessage";

export function AdminGroupMenuPage() {
  const { canRead, canWrite } = useAdminPermission("admin_group_menu");
  const [groups, setGroups] = useState<AdminGroupResponse[]>([]);
  const [menus, setMenus] = useState<AdminMenuTreeResponse[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number>(0);
  const [form, setForm] = useState<AdminGroupRequest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadDetail = async (groupId: number) => {
    const detail = await fetchAdminGroupDetail(groupId);
    setForm({
      groupName: detail.groupName,
      groupDesc: detail.groupDesc ?? "",
      useTf: detail.useTf,
      menuPermissions: detail.menuPermissions.map((permission) => ({
        menuId: permission.menuId,
        readTf: permission.readTf,
        writeTf: permission.writeTf,
        deleteTf: permission.deleteTf,
        useTf: permission.useTf,
      })),
    });
  };

  useEffect(() => {
    if (!canRead) {
      setIsLoading(false);
      return;
    }

    const loadInitialData = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");

        const [groupData, menuTree] = await Promise.all([
          fetchAdminGroupList({ page: 0, size: 100 }),
          fetchAdminMenuTree(),
        ]);

        setGroups(groupData.items);
        setMenus(menuTree);

        const firstGroupId = groupData.items[0]?.id ?? 0;
        setSelectedGroupId(firstGroupId);
        if (firstGroupId) {
          await loadDetail(firstGroupId);
        }
      } catch (error) {
        setErrorMessage(getErrorMessage(error, "권한 매핑 정보를 불러오지 못했습니다."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadInitialData();
  }, [canRead]);

  const handleGroupChange = async (groupId: number) => {
    try {
      setIsLoading(true);
      setSelectedGroupId(groupId);
      await loadDetail(groupId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "그룹 권한 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handlePermissionChange = (
    menuId: number,
    field: "readTf" | "writeTf" | "deleteTf" | "useTf",
    checked: boolean,
  ) => {
    setForm((current) => {
      if (!current) {
        return current;
      }

      const currentPermission = current.menuPermissions.find((permission) => permission.menuId === menuId) ?? {
        menuId,
        readTf: "N" as const,
        writeTf: "N" as const,
        deleteTf: "N" as const,
        useTf: "Y" as const,
      };

      const nextPermission = {
        ...currentPermission,
        [field]: checked ? "Y" : "N",
      };

      const nextPermissions = current.menuPermissions.filter((permission) => permission.menuId !== menuId);
      nextPermissions.push(nextPermission);

      return {
        ...current,
        menuPermissions: nextPermissions.sort((left, right) => left.menuId - right.menuId),
      };
    });
  };

  const handleSave = async () => {
    if (!form || !selectedGroupId) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await updateAdminGroup(selectedGroupId, form);
      await loadDetail(selectedGroupId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "권한 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  if (!canRead) {
    return (
      <div className="page-stack">
        <PageSection title="권한 매핑" description="이 화면을 조회할 권한이 없습니다.">
          <div className="form-message form-message--error">읽기 권한이 없습니다.</div>
        </PageSection>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageSection
        title="권한 매핑"
        description="admin_group의 menuPermissions와 같은 공용 권한 컴포넌트를 사용하도록 통합했습니다."
        action={
          canWrite && form ? (
            <button type="button" className="button-primary" onClick={() => void handleSave()} disabled={isSaving}>
              {isSaving ? "권한 저장 중..." : "권한 저장"}
            </button>
          ) : null
        }
      >
        {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

        <div className="toolbar">
          <select
            className="toolbar__select"
            value={selectedGroupId}
            onChange={(event) => void handleGroupChange(Number(event.target.value))}
          >
            {groups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.groupName}
              </option>
            ))}
          </select>
        </div>

        {isLoading || !form ? (
          <div className="form-message">데이터를 불러오는 중입니다.</div>
        ) : (
          <div className="permission-panel permission-panel--full">
            <div className="permission-panel__header">
              <div>
                <strong>{form.groupName}</strong>
                <span>{form.groupDesc || "그룹 설명이 없습니다."}</span>
              </div>
              <StatusBadge tone={form.useTf === "Y" ? "positive" : "warning"}>
                {form.useTf === "Y" ? "활성 그룹" : "비활성 그룹"}
              </StatusBadge>
            </div>
            <AdminGroupPermissionTable
              menus={menus}
              permissions={form.menuPermissions}
              disabled={!canWrite}
              title="그룹 권한 매핑"
              description="관리자 그룹 상세와 동일한 권한 저장 모델을 사용합니다."
              onChange={handlePermissionChange}
            />
          </div>
        )}
      </PageSection>
    </div>
  );
}
