export interface User {
  id: number;
  username: string;
  name: string;
  email: string;
  unit_id: number;
  unit_name: string;
  unit_address: string | null;
  roles: string[];
  active: boolean;
}
export interface Catalog {
  id: number;
  name: string;
  address?: string | null;
  active: boolean;
  unit_id?: number;
  description?: string | null;
}
export interface Policy {
  id: number;
  name: string;
  max_days: number;
  buffer_hours: number;
  pickup_hours: number;
  effective_from: string;
}
export interface Lookups {
  units: Catalog[];
  categories: Catalog[];
  locations: Catalog[];
  people: User[];
  policy: Policy | null;
}
export interface Asset {
  lifecycle_status: string;
  withdrawn: boolean;
  holding: boolean;
  id: number;
  name: string;
  category_id: number;
  category_name: string;
  unit_id: number;
  unit_name: string;
  unit_address: string | null;
  location_id: number;
  location_name: string;
  custodian_id: number;
  custodian_name: string;
  contact_email: string;
  description: string | null;
  condition: string;
  status: string;
  image_path: string | null;
  version: string;
  calendar?: Reservation[];
}
export interface Reservation {
  loan_id: number | null;
  start_at: string;
  end_at: string;
  overdue: boolean;
  status: string;
}
export interface Report {
  id: number;
  loan_id: number;
  kind: "GIAO" | "TRA";
  content: string;
  condition: string;
  evidence_path: string | null;
  giver_id: number;
  giver_name: string;
  receiver_id: number;
  receiver_name: string;
  giver_confirmed_at: string | null;
  receiver_confirmed_at: string | null;
  status: string;
  version: number;
}
export interface Loan {
  return_managers?: { id: number; name: string }[];
  need?: Need | null;
  id: number;
  asset_id: number;
  asset_name: string;
  category_name: string;
  asset_unit_id: number;
  asset_unit_name: string;
  borrower_id: number;
  borrower_name: string;
  borrower_unit_id: number;
  borrower_unit_name: string;
  need_id: number | null;
  purpose: string;
  start_at: string;
  end_at: string;
  status: string;
  reason: string | null;
  approver_name: string | null;
  created_at: string;
  decided_at: string | null;
  pickup_deadline: string | null;
  handed_at: string | null;
  returned_at: string | null;
  buffer_hours: number | null;
  overdue: boolean;
  asset?: Asset;
  reports?: Report[];
  policy?: Policy;
}
export interface Verification {
  id: number;
  verifier_id: number;
  verifier_name: string;
  verified_at: string;
  intended_purchase: boolean;
  purpose_met: boolean;
  conclusion: string;
  evidence_path: string | null;
}
export interface Need {
  id: number;
  unit_id: number;
  unit_name: string;
  creator_id: number;
  creator_name: string;
  category_id: number;
  category_name: string;
  purpose: string;
  start_at: string;
  end_at: string;
  alternative: string;
  evidence_path: string | null;
  purchased: boolean | null;
  status: string;
  created_at: string;
  verification: Verification | null;
  loans?: Loan[];
}
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export interface WithdrawalNotice {
  id: number;
  loan_id: number;
  asset_name: string;
  reason: string;
  created_at: string;
  read_at: string | null;
}
export interface LifecycleEvent {
  id: number;
  kind: string;
  content: string;
  basis: string | null;
  decision: string | null;
  created_at: string;
  actor_name: string;
}
export interface Indicator {
  total: number;
  avoided: number;
  rate: number | null;
  start: string;
  end: string;
  unit_name: string;
  assumptions: string[];
  rows: {
    id: number;
    purpose: string;
    category_name: string;
    creator_name: string;
    end_at: string;
    avoided: boolean;
    reason: string;
  }[];
}
export interface DashboardData {
  shared: number;
  my_open: number;
  my_holding: number;
  my_overdue: number;
  pending?: number;
  need_review?: number;
  paused?: number;
  overdue?: number;
  users?: number;
  units?: number;
  assets?: number;
  recent: Loan[];
}
