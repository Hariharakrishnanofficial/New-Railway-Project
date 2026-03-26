import React, { useEffect, useState } from 'react';
import './App.css';

const API_BASE = '/server/todo_list'; // Adjust if your proxy or deployment path differs

const FIELDS = [
  { key: 'fullName', label: 'Full Name', dbField: 'Full-Name' },
  { key: 'password', label: 'Password', dbField: 'Password' },
  { key: 'role', label: 'Role', dbField: 'Role' },
  { key: 'accountStatus', label: 'Account Status', dbField: 'Account_Status' },
  { key: 'aadharVerified', label: 'Aadhar Verified', dbField: 'Aadhar_Verified' },
  { key: 'idProofType', label: 'ID Proof Type', dbField: 'ID_Proof_Type' },
  { key: 'address', label: 'Address', dbField: 'Address' },
  { key: 'image', label: 'Image', dbField: 'Image' },
  { key: 'title', label: 'Task Title', dbField: 'item-name' },
  { key: 'status', label: 'Status', dbField: 'status' }
];

const getInputType = (key) => {
  if (key === 'aadharVerified') return 'checkbox';
  if (key === 'password') return 'password';
  return 'text';
};

function App() {
  const [todos, setTodos] = useState([]);
  const [form, setForm] = useState({});
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch all todos
  const fetchTodos = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/items`);
      const data = await res.json();
      if (data.status === 'success') {
        setTodos(data.data.todoItems);
      } else {
        setError(data.error || 'Failed to fetch todos');
      }
    } catch (e) {
      setError('Error fetching todos');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTodos();
  }, []);

  // Add new todo
  const handleAdd = async (e) => {
    e.preventDefault();
    // At least one text field must be filled (exclude checkbox)
    if (!FIELDS.some(f => {
      if (f.key === 'aadharVerified') return false;
      return (form[f.key] || '').toString().trim();
    })) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setForm({});
        fetchTodos();
      } else {
        setError(data.error || 'Failed to add item');
      }
    } catch (e) {
      setError('Error adding item');
    }
    setLoading(false);
  };

  // Start editing
  const startEdit = (todo) => {
    setEditId(todo.id);
    setEditForm(FIELDS.reduce((acc, f) => ({ ...acc, [f.key]: todo[f.key] || '' }), {}));
  };

  // Save edit
  const handleEdit = async (e) => {
    e.preventDefault();
    // At least one text field must be filled (exclude checkbox)
    if (!FIELDS.some(f => {
      if (f.key === 'aadharVerified') return false;
      return (editForm[f.key] || '').toString().trim();
    })) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/items/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setEditId(null);
        setEditForm({});
        fetchTodos();
      } else {
        setError(data.error || 'Failed to update item');
      }
    } catch (e) {
      setError('Error updating item');
    }
    setLoading(false);
  };

  // Delete todo
  const handleDelete = async (id) => {
    if (!window.confirm('Delete this item?')) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/items/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.status === 'success') {
        fetchTodos();
      } else {
        setError(data.error || 'Failed to delete item');
      }
    } catch (e) {
      setError('Error deleting item');
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <h1>TodoItems (Full Schema)</h1>
      <form onSubmit={handleAdd} style={{ marginBottom: 20 }}>
        {FIELDS.map(field => (
          <div key={field.key} style={{ marginBottom: 8 }}>
            <input
              type={getInputType(field.key)}
              value={field.key === 'aadharVerified' ? undefined : (form[field.key] || '')}
              checked={field.key === 'aadharVerified' ? form[field.key] || false : undefined}
              onChange={e => setForm(f => ({
                ...f,
                [field.key]: field.key === 'aadharVerified' ? e.target.checked : e.target.value
              }))}
              placeholder={field.label}
              disabled={loading}
              style={{ width: 220 }}
            />
            <label style={{ marginLeft: 8 }}>{field.label}</label>
          </div>
        ))}
        <button type="submit" disabled={loading || !FIELDS.some(f => {
          if (f.key === 'aadharVerified') return false; // Don't require checkbox
          return (form[f.key] || '').trim();
        })}>Add</button>
      </form>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {loading && <div>Loading...</div>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {todos.map(todo => (
          <li key={todo.id} style={{ marginBottom: 18, border: '1px solid #ccc', padding: 10, borderRadius: 6 }}>
            {editId === todo.id ? (
              <form onSubmit={handleEdit} style={{ display: 'inline-block' }}>
                {FIELDS.map(field => (
                  <div key={field.key} style={{ marginBottom: 8 }}>
                    <input
                      type={getInputType(field.key)}
                      value={field.key === 'aadharVerified' ? undefined : (editForm[field.key] || '')}
                      checked={field.key === 'aadharVerified' ? editForm[field.key] || false : undefined}
                      onChange={e => setEditForm(f => ({
                        ...f,
                        [field.key]: field.key === 'aadharVerified' ? e.target.checked : e.target.value
                      }))}
                      placeholder={field.label}
                      disabled={loading}
                      style={{ width: 220 }}
                    />
                    <label style={{ marginLeft: 8 }}>{field.label}</label>
                  </div>
                ))}
                <button type="submit" disabled={loading || !FIELDS.some(f => {
                  if (f.key === 'aadharVerified') return false;
                  return (editForm[f.key] || '').trim();
                })}>Save</button>
                <button type="button" onClick={() => setEditId(null)} disabled={loading}>Cancel</button>
              </form>
            ) : (
              <>
                <div><b>ID:</b> {todo.id}</div>
                {FIELDS.map(field => (
                  <div key={field.key}>
                    <b>{field.label}:</b> {
                      field.key === 'aadharVerified'
                        ? (todo[field.key] ? 'Yes' : 'No')
                        : (todo[field.key] || <span style={{ color: '#aaa' }}>-</span>)
                    }
                  </div>
                ))}
                <button onClick={() => startEdit(todo)} disabled={loading} style={{ marginTop: 8, marginRight: 8 }}>Edit</button>
                <button onClick={() => handleDelete(todo.id)} disabled={loading}>Delete</button>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
