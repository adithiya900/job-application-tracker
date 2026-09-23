import PropTypes from 'prop-types';

function StatusBadge({ status }) {
  const statusClass = status.toLowerCase();

  return (
    <span className={`status-badge ${statusClass}`}>
      {status}
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};

export default StatusBadge;