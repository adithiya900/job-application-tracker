export const STATUS_CONFIG = {
  APPLIED:      { label: "Applied",      badgeClass: "badge badge-applied",       icon: "📝" },
  UNDER_REVIEW: { label: "Under Review", badgeClass: "badge badge-under-review",  icon: "🔍" },
  PHONE_SCREEN: { label: "Phone Screen", badgeClass: "badge badge-phone-screen",  icon: "📞" },
  INTERVIEW:    { label: "Interview",    badgeClass: "badge badge-interview",      icon: "🎙" },
  OFFER:        { label: "Offer",        badgeClass: "badge badge-offer",          icon: "🎉" },
  REJECTED:     { label: "Rejected",     badgeClass: "badge badge-rejected",       icon: "❌" },
  WITHDRAWN:    { label: "Withdrawn",    badgeClass: "badge badge-withdrawn",      icon: "↩" },
};

export default function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { label: status, badgeClass: "badge badge-withdrawn", icon: "?" };
  return (
    <span className={config.badgeClass}>
      {config.label}
    </span>
  );
}