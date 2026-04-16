export interface DashboardMetric {
  id: string;
  label: string;
  value: number;
  hint: string;
  icon: string;
}

export interface DashboardActivity {
  id: number;
  title: string;
  owner: string;
  status: string;
  dueDate: string;
}
