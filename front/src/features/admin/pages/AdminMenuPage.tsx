import { useEffect, useMemo, useState } from "react";
import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { useAdminPermission } from "../../../hooks/useAdminPermission";
import {
  createAdminMenu,
  deleteAdminMenu,
  fetchAdminMenuDetail,
  fetchAdminMenuTree,
  updateAdminMenu,
} from "../../../services/adminMenuApi";
import type { AdminMenu, AdminMenuRequest, AdminMenuTreeResponse } from "../../../types/admin";
import { flattenMenuTree } from "../../../utils/menuTreeFlattener";
import { getErrorMessage } from "../../../utils/getErrorMessage";

const emptyForm: AdminMenuRequest = {
  parentId: null,
  menuName: "",
  menuKey: "",
  menuPath: "",
  depth: 1,
  sortNo: 1,
  icon: "",
  useTf: "Y",
  delTf: "N",
};

function sortTree(nodes: AdminMenuTreeResponse[]): AdminMenuTreeResponse[] {
  return [...nodes]
    .sort((left, right) => {
      if (left.sortNo !== right.sortNo) {
        return left.sortNo - right.sortNo;
      }

      return left.id - right.id;
    })
    .map((node) => ({
      ...node,
      children: sortTree(node.children ?? []),
    }));
}

function collectMenus(nodes: AdminMenuTreeResponse[], result: AdminMenu[] = []): AdminMenu[] {
  nodes.forEach((node) => {
    result.push({
      id: node.id,
      parentId: node.parentId ?? null,
      menuName: node.menuName,
      menuKey: node.menuKey,
      menuPath: node.menuPath ?? null,
      depth: node.depth,
      sortNo: node.sortNo,
      icon: node.icon ?? null,
      useTf: node.useTf,
      delTf: node.delTf ?? "N",
      regAdm: node.regAdm,
      regDate: node.regDate,
      upAdm: node.upAdm,
      upDate: node.upDate,
      delAdm: node.delAdm,
      delDate: node.delDate,
    });

    collectMenus(node.children ?? [], result);
  });

  return result;
}

function toRequestBody(form: AdminMenuRequest): AdminMenuRequest {
  return {
    ...form,
    parentId: form.parentId || null,
  };
}

function toRequestFromNode(node: AdminMenuTreeResponse): AdminMenuRequest {
  return {
    parentId: node.parentId ?? null,
    menuName: node.menuName,
    menuKey: node.menuKey,
    menuPath: node.menuPath ?? "",
    depth: node.depth,
    sortNo: node.sortNo,
    icon: node.icon ?? "",
    useTf: node.useTf,
    delTf: node.delTf ?? "N",
  };
}

function reorderSiblingNodes(
  nodes: AdminMenuTreeResponse[],
  draggedId: number,
  targetId: number,
): { nodes: AdminMenuTreeResponse[]; updatedNodes: AdminMenuTreeResponse[] } | null {
  const draggedIndex = nodes.findIndex((node) => node.id === draggedId);
  const targetIndex = nodes.findIndex((node) => node.id === targetId);

  if (draggedIndex >= 0 && targetIndex >= 0) {
    if (draggedIndex === targetIndex) {
      return null;
    }

    const reordered = [...nodes];
    const [movedNode] = reordered.splice(draggedIndex, 1);
    reordered.splice(targetIndex, 0, movedNode);

    const normalized = reordered.map((node, index) => ({
      ...node,
      sortNo: index + 1,
    }));

    return {
      nodes: normalized,
      updatedNodes: normalized,
    };
  }

  for (let index = 0; index < nodes.length; index += 1) {
    const currentNode = nodes[index];
    if (!currentNode.children?.length) {
      continue;
    }

    const childResult = reorderSiblingNodes(currentNode.children, draggedId, targetId);
    if (!childResult) {
      continue;
    }

    const nextNodes = [...nodes];
    nextNodes[index] = {
      ...currentNode,
      children: childResult.nodes,
    };

    return {
      nodes: nextNodes,
      updatedNodes: childResult.updatedNodes,
    };
  }

  return null;
}

export function AdminMenuPage() {
  const { canRead, canWrite, canDelete } = useAdminPermission("adm_menu");
  const [menuTree, setMenuTree] = useState<AdminMenuTreeResponse[]>([]);
  const [selectedMenuId, setSelectedMenuId] = useState<number | null>(null);
  const [form, setForm] = useState<AdminMenuRequest>(emptyForm);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const [draggedMenuId, setDraggedMenuId] = useState<number | null>(null);
  const [dragOverMenuId, setDragOverMenuId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const flattenedMenus = useMemo(() => flattenMenuTree(menuTree), [menuTree]);
  const menuList = useMemo(() => collectMenus(menuTree), [menuTree]);
  const flattenedMenuMap = useMemo(
    () => new Map(flattenedMenus.map((menu) => [menu.id, menu])),
    [flattenedMenus],
  );

  const refreshMenus = async (nextSelectedId?: number | null) => {
    const treeData = sortTree(await fetchAdminMenuTree());
    setMenuTree(treeData);

    const flatMenus = flattenMenuTree(treeData);
    const candidateId = nextSelectedId ?? selectedMenuId ?? flatMenus[0]?.id ?? null;
    setSelectedMenuId(candidateId);
    return candidateId;
  };

  const loadDetail = async (menuId: number) => {
    const detail = await fetchAdminMenuDetail(menuId);
    setForm({
      parentId: detail.parentId,
      menuName: detail.menuName,
      menuKey: detail.menuKey,
      menuPath: detail.menuPath ?? "",
      depth: detail.depth,
      sortNo: detail.sortNo,
      icon: detail.icon ?? "",
      useTf: detail.useTf,
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

        const nextId = await refreshMenus();
        if (nextId) {
          await loadDetail(nextId);
        } else {
          setIsCreating(true);
          setForm(emptyForm);
        }
      } catch (error) {
        setErrorMessage(getErrorMessage(error, "관리자 메뉴 정보를 불러오지 못했습니다."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadInitialData();
  }, [canRead]);

  const handleSelectMenu = async (menuId: number) => {
    try {
      setIsLoading(true);
      setIsCreating(false);
      setSelectedMenuId(menuId);
      await loadDetail(menuId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 메뉴 상세 정보를 불러오지 못했습니다."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateMode = (parentId: number | null = null) => {
    const siblingCount = menuList.filter((menu) => (menu.parentId ?? null) === parentId).length;

    setIsCreating(true);
    setSelectedMenuId(null);
    setForm({
      ...emptyForm,
      parentId,
      depth: parentId ? 2 : 1,
      sortNo: siblingCount + 1,
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setErrorMessage("");

      if (isCreating) {
        const created = await createAdminMenu(toRequestBody(form));
        const nextId = await refreshMenus(created.id);
        if (nextId) {
          setIsCreating(false);
          await loadDetail(nextId);
        }
        return;
      }

      if (!selectedMenuId) {
        return;
      }

      await updateAdminMenu(selectedMenuId, toRequestBody(form));
      await refreshMenus(selectedMenuId);
      await loadDetail(selectedMenuId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 메뉴 저장에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedMenuId || !window.confirm("선택한 메뉴를 삭제하시겠습니까?")) {
      return;
    }

    try {
      setIsSaving(true);
      await deleteAdminMenu(selectedMenuId);
      const nextId = await refreshMenus(null);
      if (nextId) {
        await loadDetail(nextId);
        setIsCreating(false);
      } else {
        setIsCreating(true);
        setForm(emptyForm);
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "관리자 메뉴 삭제에 실패했습니다."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleDragStart = (menuId: number) => {
    if (!canWrite) {
      return;
    }

    setDraggedMenuId(menuId);
    setDragOverMenuId(null);
    setErrorMessage("");
  };

  const handleDragEnd = () => {
    setDraggedMenuId(null);
    setDragOverMenuId(null);
  };

  const handleDrop = async (targetMenuId: number) => {
    if (!draggedMenuId || draggedMenuId === targetMenuId || !canWrite) {
      handleDragEnd();
      return;
    }

    const draggedMenu = flattenedMenuMap.get(draggedMenuId);
    const targetMenu = flattenedMenuMap.get(targetMenuId);

    if (!draggedMenu || !targetMenu || draggedMenu.parentId !== targetMenu.parentId) {
      setErrorMessage("같은 레벨의 메뉴끼리만 순서를 변경할 수 있습니다.");
      handleDragEnd();
      return;
    }

    const reordered = reorderSiblingNodes(menuTree, draggedMenuId, targetMenuId);
    if (!reordered) {
      handleDragEnd();
      return;
    }

    const nextTree = sortTree(reordered.nodes);
    setMenuTree(nextTree);

    try {
      setIsReordering(true);
      setErrorMessage("");

      for (const node of reordered.updatedNodes) {
        await updateAdminMenu(node.id, toRequestFromNode(node));
      }

      const nextId = await refreshMenus(selectedMenuId);
      if (!isCreating && nextId) {
        await loadDetail(nextId);
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "메뉴 순서 저장에 실패했습니다."));
      await refreshMenus(selectedMenuId);
    } finally {
      setIsReordering(false);
      handleDragEnd();
    }
  };

  if (!canRead) {
    return (
      <div className="page-stack">
        <PageSection title="메뉴 관리" description="이 화면을 조회할 권한이 없습니다.">
          <div className="form-message form-message--error">읽기 권한이 없습니다.</div>
        </PageSection>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageSection
        title="메뉴 관리"
        description="메뉴 트리와 상세 폼을 함께 보면서 등록, 수정, 삭제와 순서 변경까지 한 화면에서 처리합니다."
        action={
          canWrite ? (
            <button type="button" className="button-primary" onClick={() => handleCreateMode(null)}>
              메뉴 등록
            </button>
          ) : null
        }
      >
        {errorMessage ? <div className="form-message form-message--error">{errorMessage}</div> : null}

        <div className="content-grid content-grid--wide">
          <div className="table-card">
            <div className="table-card__meta">
              <p className="eyebrow">Drag and drop</p>
              <strong>최상위 메뉴는 루트끼리, 하위 메뉴는 같은 부모 아래에서만 이동됩니다.</strong>
              <span>
                {isReordering
                  ? "순서를 저장하고 있습니다..."
                  : "행을 끌어서 놓으면 순서가 바로 반영됩니다."}
              </span>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 44 }} />
                  <th>ID</th>
                  <th>메뉴명</th>
                  <th>경로</th>
                  <th>정렬</th>
                  <th>Depth</th>
                  <th>부모 ID</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {flattenedMenus.map((menu) => {
                  const isDragged = draggedMenuId === menu.id;
                  const isDropTarget = dragOverMenuId === menu.id && draggedMenuId !== menu.id;

                  return (
                    <tr
                      key={menu.id}
                      draggable={canWrite}
                      onClick={() => void handleSelectMenu(menu.id)}
                      onDragStart={() => handleDragStart(menu.id)}
                      onDragEnd={handleDragEnd}
                      onDragOver={(event) => {
                        if (!draggedMenuId || draggedMenuId === menu.id) {
                          return;
                        }

                        const draggedMenu = flattenedMenuMap.get(draggedMenuId);
                        if (!draggedMenu || draggedMenu.parentId !== menu.parentId) {
                          return;
                        }

                        event.preventDefault();
                        setDragOverMenuId(menu.id);
                      }}
                      onDragLeave={() => {
                        if (dragOverMenuId === menu.id) {
                          setDragOverMenuId(null);
                        }
                      }}
                      onDrop={(event) => {
                        event.preventDefault();
                        void handleDrop(menu.id);
                      }}
                      className={[
                        menu.id === selectedMenuId && !isCreating ? "is-selected" : "",
                        canWrite ? "is-draggable" : "",
                        isDragged ? "is-dragging" : "",
                        isDropTarget ? "is-drop-target" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      <td>
                        <span className="drag-handle" aria-hidden="true">
                          ::
                        </span>
                      </td>
                      <td>{menu.id}</td>
                      <td className="menu-name-cell">
                        <span
                          className="menu-name-cell__label"
                          style={{ paddingLeft: `${menu.level * 18}px` }}
                        >
                          {menu.level > 0 ? "ㄴ " : ""}
                          {menu.menuName}
                        </span>
                      </td>
                      <td>{menu.menuPath || "-"}</td>
                      <td>{menu.sortNo}</td>
                      <td>{menu.depth}</td>
                      <td>{menu.parentId ?? "-"}</td>
                      <td>
                        <StatusBadge tone={menu.useTf === "Y" ? "positive" : "warning"}>
                          {menu.useTf === "Y" ? "노출" : "비노출"}
                        </StatusBadge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="detail-card">
            <div className="detail-card__header">
              <div>
                <p className="eyebrow">adm_menu detail</p>
                <h3>{isCreating ? "신규 메뉴 등록" : form.menuName || "메뉴 상세"}</h3>
              </div>
              <StatusBadge tone={form.useTf === "Y" ? "positive" : "warning"}>
                {form.useTf === "Y" ? "노출" : "비노출"}
              </StatusBadge>
            </div>

            {isLoading ? <div className="form-message">데이터를 불러오는 중입니다.</div> : null}

            <div className="form-grid">
              <label>
                메뉴명
                <input
                  disabled={!canWrite}
                  value={form.menuName}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, menuName: event.target.value }))
                  }
                />
              </label>
              <label>
                메뉴 키
                <input
                  disabled={!canWrite}
                  value={form.menuKey}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, menuKey: event.target.value }))
                  }
                />
              </label>
              <label>
                라우트 경로
                <input
                  disabled={!canWrite}
                  value={form.menuPath ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, menuPath: event.target.value }))
                  }
                />
              </label>
              <label>
                아이콘 코드
                <input
                  disabled={!canWrite}
                  value={form.icon ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, icon: event.target.value }))
                  }
                />
              </label>
              <label>
                부모 메뉴
                <select
                  disabled={!canWrite}
                  value={form.parentId ?? 0}
                  onChange={(event) => {
                    const parentId = Number(event.target.value) || null;
                    const parentMenu = menuList.find((menu) => menu.id === parentId);
                    const siblingCount = menuList.filter(
                      (menu) => (menu.parentId ?? null) === parentId && menu.id !== selectedMenuId,
                    ).length;

                    setForm((current) => ({
                      ...current,
                      parentId,
                      depth: parentMenu ? parentMenu.depth + 1 : 1,
                      sortNo: siblingCount + 1,
                    }));
                  }}
                >
                  <option value={0}>최상위 메뉴</option>
                  {flattenedMenus
                    .filter((menu) => menu.id !== selectedMenuId && menu.depth === 1)
                    .map((menu) => (
                      <option key={menu.id} value={menu.id}>
                        {menu.label}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                정렬 순서
                <input value={form.sortNo} readOnly />
              </label>
              <label>
                Depth
                <input value={form.depth ?? 1} readOnly />
              </label>
              <label>
                사용 여부
                <select
                  disabled={!canWrite}
                  value={form.useTf}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      useTf: event.target.value as "Y" | "N",
                    }))
                  }
                >
                  <option value="Y">Y</option>
                  <option value="N">N</option>
                </select>
              </label>
            </div>

            <div className="detail-card__actions">
              {!isCreating && canWrite ? (
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => handleCreateMode(selectedMenuId)}
                >
                  하위 메뉴 추가
                </button>
              ) : null}
              {!isCreating && canDelete ? (
                <button type="button" className="ghost-button" onClick={handleDelete}>
                  삭제
                </button>
              ) : null}
              {canWrite ? (
                <button
                  type="button"
                  className="button-primary"
                  onClick={() => void handleSave()}
                  disabled={isSaving || isReordering}
                >
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
