import { Link } from "react-router-dom";
import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { adminService } from "../../../services/adminService";

export function AdminDashboardPage() {
  const groups = adminService.getAdminGroups();
  const users = adminService.getAdminUsers();
  const menus = adminService.getAdminMenus();
  const logs = adminService.getAdminAccessLogs();

  const stats = [
    { label: "활성 관리자", value: `${users.filter((user) => user.status === "ACTIVE").length}명`, sub: "현재 운영 계정" },
    { label: "권한 그룹", value: `${groups.length}개`, sub: "RBAC 그룹" },
    { label: "운영 메뉴", value: `${menus.filter((menu) => menu.parentId === null).length}개`, sub: "LNB 노출 기준" },
    { label: "오늘 로그", value: `${logs.filter((log) => log.createdAt.startsWith("2026-04-11")).length}건`, sub: "감사 대상" },
  ];

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Administrator Center</p>
          <h2>운영 권한과 감사 로그를 한 화면에서 관리합니다.</h2>
          <p>
            <code>admin_group</code>, <code>admin</code>, <code>adm_menu</code>,{" "}
            <code>admin_group_menu</code>, <code>admin_access_log</code> 흐름이 바로 이어지도록
            관리자 전용 레이아웃과 작업 시작 지점을 구성했습니다.
          </p>
        </div>

        <div className="hero-panel__actions">
          <Link to="/admin/groups" className="button-primary">
            그룹 관리 시작
          </Link>
          <Link to="/admin/permissions" className="ghost-button">
            권한 매핑 검토
          </Link>
        </div>
      </section>

      <section className="stats-grid">
        {stats.map((stat) => (
          <article key={stat.label} className="stat-card">
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <p>{stat.sub}</p>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <PageSection
          title="관리자 작업 흐름"
          description="테이블 기준 기능 우선순위에 맞춰 순서대로 접근할 수 있게 구성했습니다."
        >
          <div className="workflow-list">
            <div className="workflow-item">
              <strong>1. 관리자 그룹</strong>
              <span>권한 정책과 사용 여부를 정의합니다.</span>
            </div>
            <div className="workflow-item">
              <strong>2. 관리자 계정</strong>
              <span>그룹 소속과 상태값, 마지막 로그인 정보를 관리합니다.</span>
            </div>
            <div className="workflow-item">
              <strong>3. 메뉴 구조</strong>
              <span>LNB와 상하위 메뉴 경로를 설계합니다.</span>
            </div>
            <div className="workflow-item">
              <strong>4. 권한 매핑</strong>
              <span>읽기, 쓰기, 삭제 권한을 그룹별로 체크합니다.</span>
            </div>
            <div className="workflow-item">
              <strong>5. 접근 로그</strong>
              <span>로그인, 변경, 내보내기 이력을 감사 기준으로 추적합니다.</span>
            </div>
          </div>
        </PageSection>

        <PageSection
          title="최근 운영 이벤트"
          description="최근 관리자 작업과 결과 상태를 바로 확인할 수 있습니다."
        >
          <div className="log-feed">
            {logs.slice(0, 5).map((log) => (
              <div key={log.id} className="log-feed__item">
                <div>
                  <strong>{log.adminName}</strong>
                  <p>{log.message}</p>
                </div>
                <div className="log-feed__meta">
                  <StatusBadge tone={log.resultTf === "Y" ? "positive" : "danger"}>
                    {log.actionType}
                  </StatusBadge>
                  <span>{log.createdAt}</span>
                </div>
              </div>
            ))}
          </div>
        </PageSection>
      </section>
    </div>
  );
}
