# Abel AI API Key OAuth Flow

Base URL: `https://api.abel.ai/echo/`

This API key flow is designed for agents and assistants.
It is the required entrypoint whenever a skill-driven Abel API call starts without an existing user API key in session state, `--api-key`, or `.env.skills`.
Do not ask the user to manually type an email address.
Always start by requesting an agent OAuth authorization URL, send that URL back to the user, and then poll for the final result yourself.

## Agent Rules

- Always call the agent authorize endpoint first and return the `data.authUrl` value to the user.
- Do not continue to CAP probing, capability inspection, or other live Abel API calls until this authorization flow has succeeded and a user API key is available.
- The URL `GET /web/credentials/oauth/google/authorize/agent` is the backend endpoint the agent calls to obtain the authorization link. It is not the link the user should open in the browser.
- Prefer opening `data.authUrl` for the user automatically when the client supports it. Otherwise render it as a directly clickable link instead of plain text that must be copied manually.
- Never ask the user to open or click `https://api.abel.ai/echo/web/credentials/oauth/google/authorize/agent` directly. The user-facing authorization link is the Google OAuth URL returned in `data.authUrl`.
- Do not ask the user to paste an email address.
- Do not ask the user to paste the Google OAuth `code`.
- Do not try to manually complete the callback flow on behalf of the user.
- Store the returned `data.resultUrl` or `data.pollToken` so you can fetch the final authorization result after the user completes Google authorization.
- After you send the authorization link, start polling the result endpoint yourself. Do not wait for the user to reply with "authorized", "done", or similar confirmation before polling.
- Use `data.pollIntervalSeconds` when present; otherwise poll every 2 seconds until the result becomes `authorized`, `failed`, or the handoff expires.
- Treat the backend response envelope as `{ code, message, time, data }`.

## Recommended Agent Flow

If this is the first Abel use in the session, treat the missing key as a hard prerequisite and complete this flow before any live CAP usage.

1. Call `GET /web/credentials/oauth/google/authorize/agent`.
2. Read the `data.authUrl` field from the response. This returned `data.authUrl` is the user-facing authorization link.
3. Store `data.resultUrl` or `data.pollToken`.
4. Open `data.authUrl` for the user when your environment supports opening browser links directly. Otherwise reply with `data.authUrl` as a clickable link and ask them to click it to authorize with Google. Do not send the `/authorize/agent` endpoint URL itself to the user.
5. Immediately start polling `GET /web/credentials/oauth/google/result?pollToken=...` or `data.resultUrl` on the configured poll interval.
6. Continue polling while the result response is `pending` and the handoff is not expired.
7. If the result response is `authorized`, read `data.apiKey`, `data.ratePerMinute`, and `data.expireTime` from the result response, then return them to the user.
8. If the result response is `failed`, return the failure message to the user.

Only after a successful authorization result should the skill continue with CAP probing, capability discovery, or other live Abel usage.

The browser callback page only shows the authorization status and that the user can return to Abel AI. The API key is retrieved from the result endpoint, not displayed in the HTML callback page.

## Local Env File

If local storage is available, persist the authorized key in `<skill-root>/.env.skills` so later probe calls can reuse it.

Example:

```dotenv
ABEL_API_KEY=abel_xxx
CAP_BASE_URL=https://cap.abel.ai
```

This is a runtime-created local file, not a bundled artifact. Do not ship `.env.skills` or `.env.skills.example` inside the published skill bundle.

## Endpoint: Get Agent OAuth Authorization URL

Method: `GET`
Path: `/web/credentials/oauth/google/authorize/agent`
Full URL: `https://api.abel.ai/echo/web/credentials/oauth/google/authorize/agent`
Authentication: none

This endpoint is for the agent to call. The browser URL the user should open is the `data.authUrl` value returned by this endpoint, not this API URL itself.

### Success Response

```json
{
  "code": 200,
  "message": "Success",
  "time": 1773905855,
  "data": {
    "provider": "google",
    "flow": "agent_handoff",
    "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?...",
    "redirectUri": "https://api.abel.ai/echo/web/credentials/oauth/google/callback",
    "resultUrl": "https://api.abel.ai/echo/web/credentials/oauth/google/result?pollToken=POLL_TOKEN",
    "pollToken": "POLL_TOKEN",
    "authorizationState": "pending_user_action",
    "expiresAt": 1773906755,
    "expiresInSeconds": 900
  }
}
```

### Agent Behavior

When this endpoint succeeds, respond to the user like this:

`Please use this Google authorization link to get your Abel AI API key: {authUrl}. If your client supports it, open the link directly instead of asking the user to copy it. I'll keep checking and send you the key automatically once authorization completes.`

Do not send the `authorize/agent` API URL itself to the user as the authorization link.
Then keep the returned `resultUrl` or `pollToken` and poll it until authorization finishes.

Do not ask the user to paste an email address or the OAuth code.
Do not ask the user to copy and paste the authorization URL when the client can open it or render it as a clickable link.
Do not ask the user to reply in chat after they finish authorization unless you need to recover from an expired or failed handoff.

## Endpoint: Get Agent Authorization Result

Method: `GET`
Path: `/web/credentials/oauth/google/result`
Full URL: `https://api.abel.ai/echo/web/credentials/oauth/google/result?pollToken=POLL_TOKEN`
Authentication: none

### Not Ready Yet Response

```json
{
  "code": 200,
  "message": "Success",
  "time": 1773905855,
  "data": {
    "provider": "google",
    "status": "pending",
    "ready": false,
    "message": "Awaiting user authorization.",
    "authorizationState": "pending_user_action",
    "expiresAt": 1773906755
  }
}
```

### Authorized Response

```json
{
  "code": 200,
  "message": "Success",
  "time": 1773905855,
  "data": {
    "provider": "google",
    "status": "authorized",
    "ready": true,
    "message": "Authorization successful. API key is ready.",
    "authorizationState": "verified",
    "apiKey": "abel_xxx",
    "ratePerMinute": 60,
    "expireTime": 1776499200
  }
}
```

### Failed Response

```json
{
  "code": 200,
  "message": "Success",
  "time": 1773905855,
  "data": {
    "provider": "google",
    "status": "failed",
    "ready": false,
    "message": "your account is not activated",
    "authorizationState": "failed",
    "errorCode": 403
  }
}
```

## Callback Behavior

Method: `GET`
Path: `/web/credentials/oauth/google/callback`
Full URL: `https://api.abel.ai/echo/web/credentials/oauth/google/callback`
Authentication: none

This endpoint is intended to be opened in the user's browser after Google authorization.
Agents should not ask the user to copy the OAuth `code` back into chat.
For agent handoff flow, the callback page is only a confirmation page. The agent should use the saved `resultUrl` or `pollToken` to fetch the final result.

Backend behavior:

- verify the Google OAuth code
- read the verified Google identity from Google claims
- create or update the Abel AI user
- require the account to be activated
- create or reuse the API key with existing `CreateOrUpdateApiCompanyConfig` logic
- if this is the agent handoff flow, save the final authorization result for the result endpoint
- return a human-readable status page in HTML mode

Optional JSON mode:

- add `?format=json` or send `Accept: application/json`

Example:

`https://api.abel.ai/echo/web/credentials/oauth/google/callback?code=GOOGLE_CODE&format=json`

### Legacy Manual JSON Success Response

```json
{
  "code": 200,
  "message": "Success",
  "time": 1773905855,
  "data": {
    "apiKey": "abel_xxx",
    "ratePerMinute": 60,
    "expireTime": 1776499200,
    "authorizationState": "verified"
  }
}
```

Notes:

- `expireTime` in JSON is a Unix timestamp in seconds.
- The HTML callback page only renders authorization status text. It does not display the API key or account quota details.
- The agent-facing success payload only needs to expose `apiKey`, `ratePerMinute`, and `expireTime`.

## Failure Handling

- If the agent authorize endpoint fails or does not return `data.authUrl`, tell the user that the authorization link could not be created and ask them to try again later.
- If the result endpoint still returns `pending`, continue polling until the authorization completes or expires. Only tell the user it is still pending if you need to provide a progress update or stop the turn before completion.
- If the result endpoint returns `404`, tell the user the authorization handoff expired and restart from the agent authorize endpoint.
- If callback JSON returns `400` with `message` like `missing authorization code`, tell the user to restart the authorization flow from the authorize link.
- If callback JSON returns `403` with `message` like `your account is not activated`, tell the user that Google authorization succeeded but the Abel AI account is not activated yet.
- If callback JSON returns `500` during Google verification, account setup, or API key creation, tell the user to try again later.
