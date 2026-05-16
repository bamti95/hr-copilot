import { useEffect, useMemo, useState } from "react";
import { PageIntro } from "../../../common/components/PageIntro";
import { StatusPill } from "../../../common/components/StatusPill";
import { useAuthStore } from "../../../store/useAuthStore";
import { getErrorMessage } from "../../../utils/getErrorMessage";
import { ManagerBoard } from "./components/ManagerBoard";
import { EditForm } from "./components/EditForm";
import { getRoleLabel, getStatusLabel } from "./components/managerLabels";
import {
  createManager,
  deleteManager,
  fetchManagerDetail,
  fetchManagerList,
  updateManager,
  updateManagerStatus,
} from "./services/managerService";
import type {
  ManagerCreateRequest,
  ManagerFormState,
  ManagerListResponse,
  ManagerResponse,
  ManagerUpdateRequest,
} from "./types";

type FormMode = "create" | "edit" | null;

type ValidationErrors = Partial<Record<keyof ManagerFormState, string>>;

const roleOptions = [
  "SUPER_ADMIN",
  "SYSTEM-MANAGER",
  "OPS_MANAGER",
  "RECRUIT_MANAGER",
  "DOC_REVIEWER",
  "QUALITY_MANAGER",
  "PROMPT_MANAGER",
] as const;

const statusOptions = ["ACTIVE", "INACTIVE", "LOCKED"] as const;

const emptyForm: ManagerFormState = {
  loginId: "",
  password: "",
  name: "",
  email: "",
  roleType: "SYSTEM-MANAGER",
  status: "ACTIVE",
};

function normalizeValue(value: string) {
  return value.trim();
}

function nextStatus(status: string) {
  return status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
}

export default function ManagerPage() {
  const manager = useAuthStore((state) => state.manager);
  const [data, setData] = useState<ManagerListResponse>({
    items: [],
    paging: { page: 1, size: 10, totalCount: 0, totalPages: 0 },
  });
  const [formMode, setFormMode] = useState<FormMode>(null);
  const [editingManagerId, setEditingManagerId] = useState<number | null>(null);
  const [form, setForm] = useState<ManagerFormState>(emptyForm);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const canManage = useMemo(
    () => manager?.roleType === "SYSTEM-MANAGER",
    [manager?.roleType],
  );

  const syncForm = (detail: ManagerResponse) => {
    setForm({
      loginId: detail.loginId,
      password: "",
      name: detail.name,
      email: detail.email ?? "",
      roleType: detail.roleType ?? "SYSTEM-MANAGER",
      status: detail.status,
    });
  };

  const loadManagers = async () => {
    const response = await fetchManagerList({
      page: page - 1,
      size: pageSize,
      keyword: searchKeyword || undefined,
    });

    setData(response);
  };

  useEffect(() => {
    let active = true;

    const run = async () => {
      try {
        setIsLoading(true);
        setErrorMessage("");
        const response = await fetchManagerList({
          page: page - 1,
          size: pageSize,
          keyword: searchKeyword || undefined,
        });

        if (!active) {
          return;
        }

        setData(response);
      } catch (error) {
        if (!active) {
          return;
        }

        setErrorMessage(getErrorMessage(error, "관리자 목록을 불러오지 못했습니다."));
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, [page, pageSize, searchKeyword]);

  const validateForm = () => {
    const nextErrors: ValidationErrors = {};
    const loginId = normalizeValue(form.loginId);
    const name = normalizeValue(form.name);
    const email = normalizeValue(form.email);
    const password = form.password.trim();

    if (formMode === "create") {
      if (!loginId) {
        nextErrors.loginId = "로그인 ID를 입력해주세요.";
      } else if (!/^[A-Za-z0-9._-]{3,100}$/.test(loginId)) {
        nextErrors.loginId = "로그인 ID는 3자 이상 100자 이하의 영문, 숫자, ., _, -만 사용할 수 있습니다.";
      }
    }

    if (!name) {
      nextErrors.name = "이름을 입력해주세요.";
    } else if (name.length > 100) {
      nextErrors.name = "이름은 100자 이하로 입력해주세요.";
    }

    if (!email) {
      nextErrors.email = "이메일을 입력해주세요.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "올바른 이메일 형식이 아닙니다.";
    }

    if (formMode === "create" && !password) {
      nextErrors.password = "비밀번호를 입력해주세요.";
    } else if (password && password.length < 8) {
      nextErrors.password = "비밀번호는 8자 이상이어야 합니다.";
    }

    if (!roleOptions.includes(form.roleType as (typeof roleOptions)[number])) {
      nextErrors.roleType = "권한을 선택해주세요.";
    }

    if (!statusOptions.includes(form.status as (typeof statusOptions)[number])) {
      nextErrors.status = "상태를 선택해주세요.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSearchSubmit = () => {
    setPage(1);
    setSearchKeyword(normalizeValue(searchInput));
  };

  const handleCreateMode = () => {
    if (!canManage) {
      return;
    }

    setValidationErrors({});
    setErrorMessage("");
    setForm(emptyForm);
    setEditingManagerId(null);
    setFormMode("create");
  };

  const handleEdit = async (managerId: number) => {
    if (!canManage) {
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");
      setValidationErrors({});
      const detail = await fetchManagerDetail(managerId);
      syncForm(detail);
      setEditingManagerId(managerId);
      setFormMode("edit");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 상세 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelForm = () => {
    setFormMode(null);
    setEditingManagerId(null);
    setValidationErrors({});
    setForm(emptyForm);
  };

  const handleSave = async () => {
    if (!canManage || !formMode || !validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");

      const normalizedPayload = {
        loginId: normalizeValue(form.loginId),
        password: form.password.trim(),
        name: normalizeValue(form.name),
        email: normalizeValue(form.email),
        roleType: form.roleType,
        status: form.status,
      };

      if (formMode === "create") {
        const payload: ManagerCreateRequest = normalizedPayload;
        await createManager(payload);
      } else if (editingManagerId) {
        const payload: ManagerUpdateRequest = {
          name: normalizedPayload.name,
          email: normalizedPayload.email,
          roleType: normalizedPayload.roleType,
          status: normalizedPayload.status,
          password: normalizedPayload.password || undefined,
        };

        await updateManager(editingManagerId, payload);
      }

      await loadManagers();
      handleCancelForm();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleStatus = async (row: ManagerResponse) => {
    if (!canManage) {
      return;
    }

    const targetStatus = nextStatus(row.status);
    const confirmed = window.confirm(
      `${row.name} 관리자의 상태를 ${getStatusLabel(targetStatus)}로 변경하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await updateManagerStatus(row.id, { status: targetStatus });
      await loadManagers();

      if (editingManagerId === row.id && formMode === "edit") {
        setForm((current) => ({ ...current, status: targetStatus }));
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 상태 변경에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (row: ManagerResponse) => {
    if (!canManage) {
      return;
    }

    const confirmed = window.confirm(
      `${row.name} 관리자를 삭제하시겠습니까?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      await deleteManager(row.id);
      await loadManagers();

      if (editingManagerId === row.id) {
        handleCancelForm();
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = <K extends keyof ManagerFormState>(key: K, value: ManagerFormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
    setValidationErrors((current) => ({ ...current, [key]: undefined }));
  };

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="manager"
        title="관리자 관리"
        description={`목록 중심으로 관리자 계정을 조회하고, ${getRoleLabel("SYSTEM-MANAGER")} 권한인 경우에만 신규 등록, 정보 수정, 상태 변경, 논리삭제를 수행할 수 있습니다.`}
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      {!canManage ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          현재 계정은 조회만 가능합니다. {getRoleLabel("SYSTEM-MANAGER")} 권한이 있어야 등록, 수정, 상태 변경, 삭제를 수행할 수 있습니다.
        </div>
      ) : null}

      <ManagerBoard
        data={data}
        isLoading={isLoading || isSaving}
        search={searchInput}
        pageSize={pageSize}
        canManage={canManage}
        editingManagerId={editingManagerId}
        onSearchChange={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPage(1);
          setPageSize(size);
        }}
        onCreate={handleCreateMode}
        onEdit={(managerId) => void handleEdit(managerId)}
        onToggleStatus={(row) => void handleToggleStatus(row)}
        onDelete={(row) => void handleDelete(row)}
      />

      <EditForm
        isOpen={formMode !== null}
        formMode={formMode}
        form={form}
        validationErrors={validationErrors}
        isSaving={isSaving}
        roleOptions={roleOptions}
        statusOptions={statusOptions}
        onFormChange={updateField}
        onSave={() => void handleSave()}
        onCancel={handleCancelForm}
      />
    </div>
  );
}
