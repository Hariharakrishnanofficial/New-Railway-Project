import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button, Card, EmptyState, PageHeader, Select, Spinner, Badge } from '../components/UI';
import { Field, FormActions, FormApiError, FormRow } from '../components/FormFields';
import { emailAutomationApi } from '../services/api';
import { useToast } from '../context/ToastContext';

const DEFAULT_SETTINGS = {
  enabled: false,
  openai_model: 'gpt-4o-mini',
  temperature: 0.3,
  max_tokens: 220,
  max_turns: 4,
  from_address: '',
  system_prompt: '',
  signature: '',
};

const DEFAULT_SAMPLE = {
  thread_id: 'demo-thread-001',
  message_id: 'demo-message-001',
  sender_email: 'customer@example.com',
  sender_name: 'Customer',
  subject: 'Need help with my booking',
  body: 'Hi, I received your last update. Can you please clarify the refund timeline?',
  force: false,
};

function fmt(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function normalizeSettings(raw) {
  return {
    ...DEFAULT_SETTINGS,
    ...(raw || {}),
    enabled: Boolean(raw?.enabled),
    openai_model: raw?.openai_model || DEFAULT_SETTINGS.openai_model,
    temperature: Number(raw?.temperature ?? DEFAULT_SETTINGS.temperature),
    max_tokens: Number(raw?.max_tokens ?? DEFAULT_SETTINGS.max_tokens),
    max_turns: Number(raw?.max_turns ?? DEFAULT_SETTINGS.max_turns),
    from_address: raw?.from_address || '',
    system_prompt: raw?.system_prompt || '',
    signature: raw?.signature || '',
    review_keywords: Array.isArray(raw?.review_keywords) ? raw.review_keywords : [],
    no_reply_patterns: Array.isArray(raw?.no_reply_patterns) ? raw.no_reply_patterns : [],
  };
}

function StatusBadge({ status }) {
  const value = String(status || 'unknown').toLowerCase();
  const map = {
    auto_replied: { label: 'Auto replied', color: 'var(--accent-green)', bg: 'rgba(22,163,74,0.12)' },
    manual_review: { label: 'Manual review', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
    paused: { label: 'Paused', color: 'var(--text-muted)', bg: 'rgba(100,116,139,0.12)' },
    ignored: { label: 'Ignored', color: 'var(--text-muted)', bg: 'rgba(100,116,139,0.12)' },
    duplicate: { label: 'Duplicate', color: 'var(--accent-blue)', bg: 'rgba(59,130,246,0.12)' },
    error: { label: 'Error', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
    active: { label: 'Active', color: 'var(--accent-green)', bg: 'rgba(22,163,74,0.12)' },
  };
  const data = map[value] || { label: value.replace(/_/g, ' '), color: 'var(--text-muted)', bg: 'rgba(100,116,139,0.12)' };
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '4px 10px',
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 700,
      color: data.color,
      background: data.bg,
      border: `1px solid ${data.color}30`,
      whiteSpace: 'nowrap',
    }}>
      {data.label}
    </span>
  );
}

function ThreadCard({ thread }) {
  const historyCount = Array.isArray(thread.history) ? thread.history.length : 0;
  const preview = thread.last_reply_text || thread.last_error || 'No reply yet';

  return (
    <Card padding={18} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            {thread.sender_name || thread.sender_email || 'Unknown sender'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{thread.sender_email || '—'}</div>
        </div>
        <StatusBadge status={thread.status} />
      </div>

      <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600 }}>
        {thread.subject || 'No subject'}
      </div>

      <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
        {preview}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: 11, color: 'var(--text-muted)' }}>
        <span>Thread: {thread.thread_key || '—'}</span>
        <span>Turns: {thread.turn_count ?? 0}</span>
        <span>Processed: {Array.isArray(thread.processed_message_ids) ? thread.processed_message_ids.length : 0}</span>
        <span>Updated: {fmt(thread.updated_at)}</span>
      </div>

      {Array.isArray(thread.manual_review_reasons) && thread.manual_review_reasons.length > 0 && (
        <div style={{ fontSize: 12, color: '#fbbf24' }}>
          Review reasons: {thread.manual_review_reasons.join(', ')}
        </div>
      )}

      {historyCount > 0 && (
        <details>
          <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--accent-blue)' }}>
            Show thread history ({historyCount})
          </summary>
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {thread.history.slice(-6).map((item, index) => (
              <div key={index} style={{
                padding: '10px 12px',
                border: '1px solid var(--border)',
                borderRadius: 10,
                background: 'var(--bg-inset)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
                  <strong style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
                    {item.role}
                  </strong>
                  <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>{fmt(item.created_at)}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>{item.content}</div>
              </div>
            ))}
          </div>
        </details>
      )}
    </Card>
  );
}

export default function EmailAutomationPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [threads, setThreads] = useState([]);
  const [stats, setStats] = useState({});
  const [health, setHealth] = useState(null);
  const [sample, setSample] = useState(DEFAULT_SAMPLE);
  const [result, setResult] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [settingsRes, threadsRes, healthRes] = await Promise.all([
        emailAutomationApi.getSettings(),
        emailAutomationApi.getThreads({ limit: 100 }),
        emailAutomationApi.health(),
      ]);

      setSettings(normalizeSettings(settingsRes?.settings));
      setThreads(Array.isArray(threadsRes?.threads) ? threadsRes.threads : []);
      setStats(threadsRes?.stats || {});
      setHealth(healthRes || null);
    } catch (err) {
      setApiError({ error: err.message });
      addToast(err.message || 'Failed to load email automation data', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    load();
  }, [load]);

  const visibleThreads = useMemo(() => threads.slice(0, 8), [threads]);

  const handleSettingChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSampleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSample((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const saveSettings = async () => {
    setSaving(true);
    setApiError(null);
    try {
      const payload = {
        enabled: Boolean(settings.enabled),
        openai_model: settings.openai_model,
        temperature: Number(settings.temperature || 0.3),
        max_tokens: Number(settings.max_tokens || 220),
        max_turns: Number(settings.max_turns || 4),
        from_address: settings.from_address,
        system_prompt: settings.system_prompt,
        signature: settings.signature,
      };
      const res = await emailAutomationApi.saveSettings(payload);
      setSettings(normalizeSettings(res?.settings));
      addToast('Email automation settings saved', 'success');
      await load();
    } catch (err) {
      setApiError({ error: err.message });
      addToast(err.message || 'Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const processSample = async () => {
    setProcessing(true);
    setApiError(null);
    setResult(null);
    try {
      const res = await emailAutomationApi.processReply({
        thread_id: sample.thread_id,
        message_id: sample.message_id,
        sender_email: sample.sender_email,
        sender_name: sample.sender_name,
        subject: sample.subject,
        body: sample.body,
        force: Boolean(sample.force),
      });
      setResult(res);
      addToast(res?.status === 'auto_replied' ? 'Auto-reply generated' : `Status: ${res?.status || 'unknown'}`, 'success');
      await load();
    } catch (err) {
      setApiError({ error: err.message });
      addToast(err.message || 'Failed to process sample reply', 'error');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <PageHeader
        icon="robot"
        iconAccent="var(--accent-blue)"
        title="Email Automation"
        subtitle="Auto-response from customer replies using ChatGPT/OpenAI"
      >
        <Button icon="refresh" variant="ghost" size="sm" onClick={load} disabled={loading || saving || processing}>
          Refresh
        </Button>
        <Button icon="check" variant="primary" accent="var(--accent-green)" size="sm" onClick={saveSettings} disabled={saving || loading}>
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </PageHeader>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 16 }}>
        <Card>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Auto-response</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: settings.enabled ? 'var(--accent-green)' : '#f59e0b' }}>
            {settings.enabled ? 'ON' : 'OFF'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>Live sending from inbound replies</div>
        </Card>
        <Card>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Threads tracked</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-blue)' }}>{stats.total_threads ?? threads.length}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>Persisted in Settings rows</div>
        </Card>
        <Card>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Manual review</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: '#f59e0b' }}>{stats.manual_review ?? 0}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>Escalated or risky messages</div>
        </Card>
        <Card>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>OpenAI</div>
          <div style={{ fontSize: 28, fontWeight: 800, color: health?.configured ? 'var(--accent-green)' : '#ef4444' }}>
            {health?.configured ? 'READY' : 'MISSING'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>
            {health?.model || settings.openai_model || 'Model not configured'}
          </div>
        </Card>
      </div>

      {apiError && <FormApiError response={apiError} />}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 18, alignItems: 'start' }}>
        <Card>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            Automation Settings
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 12, marginBottom: 16, background: 'var(--bg-inset)' }}>
            <input
              type="checkbox"
              name="enabled"
              checked={Boolean(settings.enabled)}
              onChange={handleSettingChange}
              style={{ width: 18, height: 18, accentColor: 'var(--accent-blue)' }}
            />
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Enable auto-response</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>When on, every qualifying inbound reply is handled automatically.</div>
            </div>
          </div>

          <FormRow cols={2}>
            <Field label="OpenAI model" name="openai_model" value={settings.openai_model} onChange={handleSettingChange} placeholder="gpt-4o-mini" />
            <Field label="From address" name="from_address" value={settings.from_address} onChange={handleSettingChange} placeholder="support@company.com" />
          </FormRow>

          <FormRow cols={3}>
            <Field label="Temperature" name="temperature" type="number" value={settings.temperature} onChange={handleSettingChange} placeholder="0.3" />
            <Field label="Max tokens" name="max_tokens" type="number" value={settings.max_tokens} onChange={handleSettingChange} placeholder="220" />
            <Field label="Max turns" name="max_turns" type="number" value={settings.max_turns} onChange={handleSettingChange} placeholder="4" />
          </FormRow>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10, marginTop: 14 }}>
            <div>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                System prompt
              </label>
              <textarea
                name="system_prompt"
                value={settings.system_prompt}
                onChange={handleSettingChange}
                rows={6}
                style={{
                  width: '100%',
                  resize: 'vertical',
                  background: 'var(--bg-inset)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: '12px 14px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                Signature
              </label>
              <textarea
                name="signature"
                value={settings.signature}
                onChange={handleSettingChange}
                rows={3}
                placeholder="Best regards, MailBot"
                style={{
                  width: '100%',
                  resize: 'vertical',
                  background: 'var(--bg-inset)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: '12px 14px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              />
            </div>
          </div>

          <FormActions
            onCancel={load}
            onSubmit={saveSettings}
            submitLabel={saving ? 'Saving...' : 'Save Settings'}
            loading={saving}
            accent="var(--accent-blue)"
          />
        </Card>

        <Card>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            Test Inbound Reply
          </div>

          <div style={{ display: 'grid', gap: 12 }}>
            <FormRow cols={2}>
              <Field label="Thread ID" name="thread_id" value={sample.thread_id} onChange={handleSampleChange} placeholder="thread id" />
              <Field label="Message ID" name="message_id" value={sample.message_id} onChange={handleSampleChange} placeholder="message id" />
            </FormRow>
            <FormRow cols={2}>
              <Field label="Sender email" name="sender_email" value={sample.sender_email} onChange={handleSampleChange} placeholder="customer@example.com" />
              <Field label="Sender name" name="sender_name" value={sample.sender_name} onChange={handleSampleChange} placeholder="Customer" />
            </FormRow>
            <Field label="Subject" name="subject" value={sample.subject} onChange={handleSampleChange} placeholder="Subject" />
            <div>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                Reply body
              </label>
              <textarea
                name="body"
                value={sample.body}
                onChange={handleSampleChange}
                rows={7}
                style={{
                  width: '100%',
                  resize: 'vertical',
                  background: 'var(--bg-inset)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: '12px 14px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input
                id="force_process"
                type="checkbox"
                name="force"
                checked={Boolean(sample.force)}
                onChange={handleSampleChange}
                style={{ width: 16, height: 16, accentColor: 'var(--accent-blue)' }}
              />
              <label htmlFor="force_process" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Force process even if risk rules would escalate
              </label>
            </div>

            <Button icon="zap" variant="primary" accent="var(--accent-blue)" onClick={processSample} disabled={processing}>
              {processing ? 'Processing...' : 'Process Reply'}
            </Button>
          </div>

          {result && (
            <div style={{ marginTop: 16, padding: 14, background: 'var(--bg-inset)', border: '1px solid var(--border)', borderRadius: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 10 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>Result</div>
                <StatusBadge status={result.status} />
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {result.reply_text || result.reason || result.error || 'No reply text returned'}
              </div>
            </div>
          )}
        </Card>
      </div>

      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Recent Threads</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Latest persisted automation state and thread history</div>
          </div>
          <Button icon="refresh" variant="ghost" size="sm" onClick={load} disabled={loading}>
            Reload
          </Button>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 36 }}>
            <Spinner />
          </div>
        ) : visibleThreads.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
            {visibleThreads.map((thread) => (
              <ThreadCard key={thread.thread_key || thread.record_id} thread={thread} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon="robot"
            title="No automated threads yet"
            description="Process a sample reply or wait for the first inbound thread to appear here."
          />
        )}
      </Card>
    </div>
  );
}
