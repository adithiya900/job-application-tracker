import { useState } from 'react';

import ApplicationCard from '../components/ApplicationCard';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Card from '../components/Card';
import Input from '../components/Input';
import StatusBadge from '../components/StatusBadge';

function ComponentsDemo() {
  const [name, setName] = useState('');

  const application = {
    jobTitle: 'Software Developer',
    company: 'ABC Technologies',
    status: 'Interview',
    appliedDate: '2026-09-23',
    location: 'Coimbatore',
  };

  return (
    <div>
      <h1>Reusable Components Demo</h1>

      <h2>Button</h2>
      <Button
        text="Click Me"
        onClick={() => console.log('Button clicked')}
      />

      <h2>Input</h2>
      <Input
        label="Name"
        placeholder="Enter your name"
        value={name}
        onChange={(event) => setName(event.target.value)}
      />

      <p>Entered Name: {name}</p>

      <h2>Card</h2>
      <Card>
        <h3>Sample Card</h3>
        <p>This is a reusable Card component.</p>
      </Card>

      <h2>Badge</h2>
      <Badge text="Active" />

      <h2>StatusBadge</h2>
      <StatusBadge status="Applied" />
      <StatusBadge status="Interview" />
      <StatusBadge status="Selected" />
      <StatusBadge status="Rejected" />

      <h2>ApplicationCard</h2>
      <ApplicationCard application={application} />
    </div>
  );
}

export default ComponentsDemo;
