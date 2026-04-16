import { PageSection } from "../../../components/common/PageSection";
import { StatusBadge } from "../../../components/common/StatusBadge";
import { adminService } from "../../../services/adminService";

export function AdminAccessLogPage() {
  const logs = adminService.getAdminAccessLogs();

  return (
    <div className="page-stack">
      <PageSection
        title="접근 로그"
        description="로그인, 수정, 삭제, 내보내기 같은 관리자 행동 이력을 감사 기준으로 추적합니다."
        action={<button type="button" className="ghost-button">CSV 다운로드</button>}
      >
        <div className="toolbar">
          <input className="toolbar__search" placeholder="관리자명, 액션, 타깃 검색" />
          <select className="toolbar__select" defaultValue="ALL">
            <option value="ALL">전체 액션</option>
            <option value="LOGIN">LOGIN</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
            <option value="EXPORT">EXPORT</option>
          </select>
          <select className="toolbar__select" defaultValue="ALL">
            <option value="ALL">전체 결과</option>
            <option value="Y">성공</option>
            <option value="N">실패</option>
          </select>
        </div>

        <div className="table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>일시</th>
                <th>관리자</th>
                <th>액션</th>
                <th>대상</th>
                <th>IP</th>
                <th>결과</th>
                <th>메시지</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.createdAt}</td>
                  <td>{log.adminName}</td>
                  <td>{log.actionType}</td>
                  <td>{log.actionTarget}</td>
                  <td>{log.ipAddress}</td>
                  <td>
                    <StatusBadge tone={log.resultTf === "Y" ? "positive" : "danger"}>
                      {log.resultTf === "Y" ? "성공" : "실패"}
                    </StatusBadge>
                  </td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageSection>
    </div>
  );
}
