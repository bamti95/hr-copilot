import { useEffect, useState } from "react";
import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { useAdminPermission } from "../../../hooks/useAdminPermission";
import { fetchAdminGroupList } from "../../../services/adminGroupService";
import {
  createAdmin,
  deleteAdmin,
  fetchAdminDetail,
  fetchAdminList,
  updateAdmin,
} from "../../../services/adminUserService";
import type { AdminGroupResponse, AdminRequest, AdminResponse } from "../../../types/admin";
import { getErrorMessage } from "../../../utils/getErrorMessage";

const emptyForm: AdminRequest = {
  groupId: 0,
  loginId: "",
  password: "",
  name: "",
  email: "",
  status: "ACTIVE",
  useTf: "Y",
  delTf: "N",
};

export function AdminUserPage() {
  const { canRead, canWrite, canDelete } = useAdminPermission("admin");
  const [admins, setAdmins] = useState<AdminResponse[]>([]);
  const [groups, setGroups] = useState<AdminGroupResponse[]>([]);
  const [selectedAdminId, setSelectedAdminId] = useState<number | null>(null);
  const [form, setForm] = useState<AdminRequest>(emptyForm);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadAdminList = async (nextSelectedId?: number | null) => {
    const data = await fetchAdminList({ page: 0, size: 100 });
    setAdmins(data.items);

    const candidateId = nextSelectedId ?? selectedAdminId ?? data.items[0]?.id ?? null;
    setSelectedAdminId(candidateId);
    return candidateId;
  };

  const loadAdminDetail = async (adminId: number) => {
    const detail = await fetchAdminDetail(adminId);
    setForm({
      groupId: detail.groupId,
      loginId: detail.loginId,
      password: "",
      name: detail.name,
      email: detail.email ?? "",
      status: detail.status,
      useTf: detail.useTf ?? "Y",
      delTf: detail.delTf ?? "N",
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

        const groupData = await fetchAdminGroupList({ page: 0, size: 100, useTf: "Y" });
        setGroups(groupData.items);

        const nextId = await loadAdminList();
        if (nextId) {
          await loadAdminDetail(nextId);
        } else {
          setIsCreating(true);
          setForm({
            ...emptyForm,
            groupId: groupData.items[0]?.id ?? 0,
          });
        }
      } catch (error) {
        setErrorMessage(getErrorMessage(error, "관리자 계정 정보를 불러오지 못했습니다."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadInitialData();
  }, [canRead]);

  const handleSelectAdmin = async (adminId: number) => {
    try {
      setIsLoading(true);
      setIsCreating(false);
      setSelectedAdminId(adminId);
      await loadAdminDetail(adminId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 상세 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateMode = () => {
    setIsCreating(true);
    setSelectedAdminId(null);
    setForm({
      ...emptyForm,
      groupId: groups[0]?.id ?? 0,
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setErrorMessage("");

      if (isCreating) {
        const created = await createAdmin(form);
        const nextId = await loadAdminList(created.id);
        if (nextId) {
          setIsCreating(false);
          await loadAdminDetail(nextId);
        }
        return;
      }

      if (!selectedAdminId) {
        return;
      }

      await updateAdmin(selectedAdminId, {
        ...form,
        password: form.password || undefined,
      });
      await loadAdminList(selectedAdminId);
      await loadAdminDetail(selectedAdminId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 계정 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedAdminId || !window.confirm("선택한 관리자 계정을 삭제하시겠습니까?")) {
      return;
    }

    try {
      setIsSaving(true);
      await deleteAdmin(selectedAdminId);
      const nextId = await loadAdminList(null);

      if (nextId) {
        await loadAdminDetail(nextId);
        setIsCreating(false);
      } else {
        handleCreateMode();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 계정 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  if (!canRead) {
    return (
      <div className="page-stack">
        <PageSection title="관리자 계정" description="이 화면을 조회할 권한이 없습니다.">
          <div className="form-message form-message--error">읽기 권한이 없습니다.</div>
        </PageSection>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageSection
        title="관리자 계정"
        description="백엔드 Admin Response/ListResponse 기준으로 관리자 정보 CRUD를 실제 API 호출로 연결했습니다."
        action={
          canWrite ? (
            <button type="button" className="button-primary" onClick={handleCreateMode}>
              관리자 등록
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
                  <th>로그인 ID</th>
                  <th>이름</th>
                  <th>그룹 ID</th>
                  <th>상태</th>
                  <th>최근 로그인</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((admin) => (
                  <tr
                    key={admin.id}
                    onClick={() => void handleSelectAdmin(admin.id)}
                    className={admin.id === selectedAdminId && !isCreating ? "is-selected" : ""}
                  >
                    <td>{admin.id}</td>
                    <td>{admin.loginId}</td>
                    <td>{admin.name}</td>
                    <td>{admin.groupId}</td>
                    <td>
                      <StatusBadge tone={admin.status === "ACTIVE" ? "positive" : admin.status === "LOCKED" ? "danger" : "warning"}>
                        {admin.status}
                      </StatusBadge>
                    </td>
                    <td>{admin.lastLoginAt ? admin.lastLoginAt.slice(0, 16).replace("T", " ") : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="detail-card">
            <div className="detail-card__header">
              <div>
                <p className="eyebrow">admin detail</p>
                <h3>{isCreating ? "신규 관리자 등록" : form.name || "관리자 상세"}</h3>
              </div>
              <StatusBadge tone={form.status === "ACTIVE" ? "positive" : form.status === "LOCKED" ? "danger" : "warning"}>
                {form.status}
              </StatusBadge>
            </div>

            {isLoading ? <div className="form-message">데이터를 불러오는 중입니다.</div> : null}

            <div className="form-grid">
              <label>
                로그인 ID
                <input disabled={!canWrite} value={form.loginId} onChange={(event) => setForm((current) => ({ ...current, loginId: event.target.value }))} />
              </label>
              <label>
                그룹
                <select disabled={!canWrite} value={form.groupId} onChange={(event) => setForm((current) => ({ ...current, groupId: Number(event.target.value) }))}>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.groupName}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                이름
                <input disabled={!canWrite} value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
              </label>
              <label>
                이메일
                <input disabled={!canWrite} value={form.email ?? ""} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} />
              </label>
              <label>
                비밀번호
                <input disabled={!canWrite} type="password" value={form.password ?? ""} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} placeholder={isCreating ? "필수 입력" : "변경 시에만 입력"} />
              </label>
              <label>
                상태
                <select disabled={!canWrite} value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value as AdminRequest["status"] }))}>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="LOCKED">LOCKED</option>
                  <option value="INACTIVE">INACTIVE</option>
                </select>
              </label>
              <label>
                사용 여부
                <select disabled={!canWrite} value={form.useTf} onChange={(event) => setForm((current) => ({ ...current, useTf: event.target.value as "Y" | "N" }))}>
                  <option value="Y">Y</option>
                  <option value="N">N</option>
                </select>
              </label>
            </div>

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
