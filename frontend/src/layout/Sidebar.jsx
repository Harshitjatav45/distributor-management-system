import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { NAV_SECTIONS } from './navConfig';

export default function Sidebar({ open, onNavigate }) {
  const { user } = useAuth();

  return (
    <aside className={`sidebar${open ? ' open' : ''}`}>
      <div className="sidebar-brand">DMS &middot; ERP</div>
      <nav className="sidebar-nav">
        {NAV_SECTIONS.map((section, idx) => {
          const visibleItems = section.items.filter(
            (item) => !item.roles || item.roles.includes(user?.role)
          );
          if (visibleItems.length === 0) return null;
          return (
            <div key={idx}>
              {section.label && <div className="sidebar-section-label">{section.label}</div>}
              {visibleItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
                  onClick={onNavigate}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
