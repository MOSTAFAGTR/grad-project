export const DEFAULT_PAYLOADS: Record<string, string> = {
  'SQL Injection': "' OR 1=1 --",
  XSS: "<script>alert('Hacked')</script>",
  'Command Injection': '8.8.8.8; cat /etc/passwd',
  CSRF: 'POST /transfer amount=1000&to_user=attacker',
};

export const getDefaultPayload = (vulnerabilityType: string): string => {
  if (DEFAULT_PAYLOADS[vulnerabilityType]) {
    return DEFAULT_PAYLOADS[vulnerabilityType];
  }

  const normalized = (vulnerabilityType || '').trim().toLowerCase();
  const mappedKey = Object.keys(DEFAULT_PAYLOADS).find((key) => key.toLowerCase() === normalized);
  return mappedKey ? DEFAULT_PAYLOADS[mappedKey] : '';
};

