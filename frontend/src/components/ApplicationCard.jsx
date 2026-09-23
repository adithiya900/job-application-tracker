import { useState } from 'react';
import PropTypes from 'prop-types';

import Card from './Card';
import StatusBadge from './StatusBadge';

function ApplicationCard({ application }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <Card>
      <h2>{application.jobTitle}</h2>
      <p>{application.company}</p>

      <StatusBadge status={application.status} />

      <button onClick={() => setShowDetails(!showDetails)}>
        {showDetails ? 'Hide Details' : 'Show Details'}
      </button>

      {showDetails && (
        <div>
          <p>Applied Date: {application.appliedDate}</p>
          <p>Location: {application.location}</p>
        </div>
      )}
    </Card>
  );
}

ApplicationCard.propTypes = {
  application: PropTypes.shape({
    jobTitle: PropTypes.string.isRequired,
    company: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    appliedDate: PropTypes.string.isRequired,
    location: PropTypes.string.isRequired,
  }).isRequired,
};

export default ApplicationCard;