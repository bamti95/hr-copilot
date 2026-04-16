import { useEffect, useState } from "react";
import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { AdminGroupPermissionTable } from "../../admin/AdminGroup/components/AdminGroupPermissionTable.tsx";
import { useAdminPermission } from "../../../hooks/useAdminPermission";
import {
  createAdminGroup,
  deleteAdminGroup,
  fetchAdminGroupDetail,
  fetchAdminGroupList,
  updateAdminGroup,
} from "../../../services/adminGroupService";
import { fetchAdminMenuTree } from "../../../services/adminMenuApi";
import type { AdminGroupRequest, AdminGroupResponse, AdminMenuTreeResponse } from "../../../types/admin";
import { getErrorMessage } from "../../../utils/getErrorMessage";

const emptyForm: AdminGroupRequest = {
  groupName: "",
  groupDesc: "",
  useTf: "Y",
  menuPermissions: [],
};

export function AdminGroupPage() {
  const { canRead, canWrite, canDelete } = useAdminPermission("admin_group");
  const [groups, setGroups] = useState<AdminGroupResponse[]>([]);
  const [menus, setMenus] = useState<AdminMenuTreeResponse[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [form, setForm] = useState<AdminGroupRequest>(emptyForm);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadGroupList = async (nextSelectedId?: number | null) => {
    const data = await fetchAdminGroupList({ page: 0, size: 100 });
    setGroups(data.items);

    const candidateId = nextSelectedId ?? selectedGroupId ?? data.items[0]?.id ?? null;
    setSelectedGroupId(candidateId);
    return candidateId;
  };

  const loadGroupDetail = async (groupId: number) => {
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

        const menuTree = await fetchAdminMenuTree();
        setMenus(menuTree);

        const nextId = await loadGroupList();
        if (nextId) {
          await loadGroupDetail(nextId);
        } else {
          setIsCreating(true);
          setForm(emptyForm);
        }
      } catch (error) {
        setErrorMessage(getErrorMessage(error, "관리자 그룹 정보를 불러오지 못했습니다."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadInitialData();
  }, [canRead]);

  const handleSelectGroup = async (groupId: number) => {
    try {
      setIsLoading(true);
      setIsCreating(false);
      setSelectedGroupId(groupId);
      await loadGroupDetail(groupId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 그룹 상세 정보를 불러오지 못했습니다."));
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

  const handleCreateMode = () => {
    setIsCreating(true);
    setSelectedGroupId(null);
    setForm(emptyForm);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setErrorMessage("");

      if (isCreating) {
        const created = await createAdminGroup(form);
        const nextId = await loadGroupList(created.id);
        if (nextId) {
          setIsCreating(false);
          await loadGroupDetail(nextId);
        }
        return;
      }

      if (!selectedGroupId) {
        return;
      }

      await updateAdminGroup(selectedGroupId, form);
      await loadGroupList(selectedGroupId);
      await loadGroupDetail(selectedGroupId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 그룹 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedGroupId || !window.confirm("선택한 관리자 그룹을 삭제하시겠습니까?")) {
      return;
    }

    try {
      setIsSaving(true);
      await deleteAdminGroup(selectedGroupId);
      const nextId = await loadGroupList(null);

      if (nextId) {
        await loadGroupDetail(nextId);
        setIsCreating(false);
      } else {
        setIsCreating(true);
        setForm(emptyForm);
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 그룹 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  if (!canRead) {
    return (
      <div className="page-stack">
        <PageSection title="관리자 그룹" description="이 화면을 조회할 권한이 없습니다.">
          <div className="form-message form-message--error">읽기 권한이 없습니다.</div>
        </PageSection>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageSection
        title="관리자 그룹"
        description="백엔드 Response/ListResponse에 맞춰 그룹 조회, 상세, 메뉴 권한 저장까지 실제 호출로 연결했습니다."
        action={
          canWrite ? (
            <button type="button" className="button-primary" onClick={handleCreateMode}>
              그룹 추가
            </button>
          ) : null
        }
      >
        {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

        <div className="content-grid content-grid--wide">
          <div className="table-card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>그룹명</th>
                  <th>설명</th>
                  <th>사용</th>
                  <th>등록일</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <tr
                    key={group.id}
                    onClick={() => void handleSelectGroup(group.id)}
                    className={group.id === selectedGroupId && !isCreating ? "is-selected" : ""}
                  >
                    <td>{group.id}</td>
                    <td>{group.groupName}</td>
                    <td>{group.groupDesc || "-"}</td>
                    <td>
                      <StatusBadge tone={group.useTf === "Y" ? "positive" : "warning"}>
                        {group.useTf === "Y" ? "사용" : "중지"}
                      </StatusBadge>
                    </td>
                    <td>{group.regDate?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="detail-card">
            <div className="detail-card__header">
              <div>
                <p className="eyebrow">admin_group detail</p>
                <h3>{isCreating ? "신규 그룹 등록" : form.groupName || "그룹 상세"}</h3>
              </div>
              <StatusBadge tone={form.useTf === "Y" ? "positive" : "warning"}>
                {form.useTf === "Y" ? "활성" : "비활성"}
              </StatusBadge>
            </div>

            {isLoading ? <div className="form-message">데이터를 불러오는 중입니다.</div> : null}

            <div className="form-grid">
              <label>
                그룹명
                <input
                  disabled={!canWrite}
                  value={form.groupName}
                  onChange={(event) => setForm((current) => ({ ...current, groupName: event.target.value }))}
                />
              </label>
              <label>
                사용 여부
                <select
                  disabled={!canWrite}
                  value={form.useTf}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, useTf: event.target.value as "Y" | "N" }))
                  }
                >
                  <option value="Y">Y</option>
                  <option value="N">N</option>
                </select>
              </label>
              <label className="form-grid__full">
                그룹 설명
                <textarea
                  disabled={!canWrite}
                  rows={3}
                  value={form.groupDesc ?? ""}
                  onChange={(event) => setForm((current) => ({ ...current, groupDesc: event.target.value }))}
                />
              </label>
            </div>

            <AdminGroupPermissionTable
              menus={menus}
              permissions={form.menuPermissions}
              disabled={!canWrite}
              description="admin_group_menu와 동일한 권한 구조를 공유합니다."
              onChange={handlePermissionChange}
            />

            <div className="detail-card__actions">
              {!isCreating && canDelete ? (
                <button type="button" className="ghost-button" onClick={handleDelete}>
                  삭제
                </button>
              ) : null}
              {canWrite ? (
                <button type="button" className="ghost-button" onClick={handleCreateMode}>
                  새로 작성
                </button>
              ) : null}
              {canWrite ? (
                <button type="button" className="button-primary" onClick={() => void handleSave()} disabled={isSaving}>
                  {isSaving ? "저장 중..." : "저장"}
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </PageSection>
    </div>
  );
}
