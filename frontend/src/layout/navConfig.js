// roles: null means every authenticated role (Admin/Manager/Staff) can see
// the link. This only controls what's SHOWN - every page and every API
// call is still independently authorized by the backend regardless of
// what's rendered here.
export const NAV_SECTIONS = [
  {
    label: null,
    items: [
      { label: 'Dashboard', path: '/dashboard', roles: null },
    ],
  },
  {
    label: 'Master Data',
    items: [
      { label: 'Companies', path: '/companies', roles: null },
      { label: 'Categories', path: '/categories', roles: null },
      { label: 'Materials', path: '/materials', roles: null },
      { label: 'Suppliers', path: '/suppliers', roles: null },
      { label: 'Customers', path: '/customers', roles: null },
    ],
  },
  {
    label: 'Inventory',
    items: [
      { label: 'Stock', path: '/stock', roles: null },
    ],
  },
  {
    label: 'Transactions',
    items: [
      { label: 'Purchases', path: '/purchases', roles: null },
      { label: 'Sales', path: '/sales', roles: null },
      { label: 'Payments', path: '/payments', roles: ['Admin', 'Manager'] },
      { label: 'Dispatch', path: '/dispatch', roles: null },
    ],
  },
  {
    label: 'Financial',
    items: [
      { label: 'Ledger', path: '/ledger', roles: ['Admin', 'Manager'] },
      { label: 'Reports', path: '/reports', roles: ['Admin', 'Manager'] },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Users', path: '/users', roles: ['Admin'] },
      { label: 'Audit Log', path: '/audit-log', roles: ['Admin'] },
    ],
  },
];
