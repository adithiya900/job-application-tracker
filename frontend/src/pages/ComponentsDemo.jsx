import { useState } from 'react';

import ApplicationCard from '../components/ApplicationCard';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Card from '../components/Card';
import Input from '../components/Input';
import StatusBadge from '../components/StatusBadge';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

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
      <h2>Table</h2>

<div className="rounded-md border">
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Company</TableHead>
        <TableHead>Role</TableHead>
        <TableHead>Status</TableHead>
        <TableHead>Applied Date</TableHead>
        <TableHead>Location</TableHead>
      </TableRow>
    </TableHeader>

    <TableBody>
      <TableRow>
        <TableCell>{application.company}</TableCell>
        <TableCell>{application.jobTitle}</TableCell>
        <TableCell>{application.status}</TableCell>
        <TableCell>{application.appliedDate}</TableCell>
        <TableCell>{application.location}</TableCell>
      </TableRow>
    </TableBody>
  </Table>
</div>
    </div>
  );
}

export default ComponentsDemo;
