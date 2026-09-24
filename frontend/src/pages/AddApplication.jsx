import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useApplications } from '../contexts/ApplicationContext';

const applicationSchema = z.object({
  company: z.string().min(2, 'Company name is required'),
  role: z.string().min(2, 'Role is required'),
  status: z.enum(['Applied', 'Interview', 'Selected', 'Rejected'], {
    error: 'Please select a valid status',
  }),
  date: z.string().min(1, 'Date is required'),
  notes: z.string().min(1, 'Notes are required'),
});

function AddApplication() {
  const [formNote, setFormNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [createdApplication, setCreatedApplication] = useState(null);

  const { applications, addApplicationOptimistically } = useApplications();
  const pendingApplication = applications.find((application) => application.optimistic);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(applicationSchema),
  });

  const onSubmit = async (data) => {
    try {
      setSubmitting(true);
      setSubmitError('');
      setCreatedApplication(null);

      const statusMap = {
        Applied: 'APPLIED',
        Interview: 'INTERVIEW',
        Selected: 'OFFER',
        Rejected: 'REJECTED',
      };

      const created = await addApplicationOptimistically({
        company: data.company,
        role: data.role,
        status: statusMap[data.status],
        notes: data.notes,
        applied_date: data.date,
      });

      setCreatedApplication(created);
      console.log('Application created successfully');
    } catch (error) {
      console.error('Failed to create application:', error);
      setSubmitError('Failed to create application. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <h1>Add Application</h1>

      {submitError && (
        <p className="form-error">{submitError}</p>
      )}

      {(pendingApplication || createdApplication) && (
        <div>
          <h3>{(pendingApplication || createdApplication).company}</h3>
          <p>{(pendingApplication || createdApplication).role}</p>
          <p>{(pendingApplication || createdApplication).status}</p>
          {pendingApplication && <p>Saving...</p>}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label htmlFor="company">Company</label>
          <input
            id="company"
            type="text"
            {...register('company')}
          />

          {errors.company && (
            <p className="form-error">{errors.company.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="role">Role</label>
          <input
            id="role"
            type="text"
            {...register('role')}
          />

          {errors.role && (
            <p className="form-error">{errors.role.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="status">Status</label>

          <select id="status" {...register('status')}>
            <option value="">Select Status</option>
            <option value="Applied">Applied</option>
            <option value="Interview">Interview</option>
            <option value="Selected">Selected</option>
            <option value="Rejected">Rejected</option>
          </select>

          {errors.status && (
            <p className="form-error">{errors.status.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="date">Date</label>
          <input
            id="date"
            type="date"
            {...register('date')}
          />

          {errors.date && (
            <p className="form-error">{errors.date.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="notes">Notes</label>

          <textarea
            id="notes"
            rows="4"
            {...register('notes')}
            onChange={(event) => setFormNote(event.target.value)}
          />

          <p>Characters: {formNote.length}</p>

          {errors.notes && (
            <p className="form-error">{errors.notes.message}</p>
          )}
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add Application'}
        </button>
      </form>
    </div>
  );
}

export default AddApplication;
