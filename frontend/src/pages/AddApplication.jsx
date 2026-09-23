import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

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

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(applicationSchema),
  });

  const onSubmit = (data) => {
    console.log('Application data:', data);
  };

  return (
    <div>
      <h1>Add Application</h1>

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

        <button type="submit">Add Application</button>
      </form>
    </div>
  );
}

export default AddApplication;