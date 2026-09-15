# Confluence Operations - Call Recipes

Concrete Atlassian calls through Executor. The v1 examples use
`tools.atlassian_mcp.org.localatlassianmcp.*` from the Executor sandbox. All
examples use `cloudId = "example.atlassian.net"`. Every successful result needs
`JSON.parse(result.data.content[0].text)` to reach the real payload.

## Preferred spaces

- the user's personal space and blog posts:
  `https://example.atlassian.net/wiki/spaces/~your-account/overview`
  Current the user account ID: `712020:ac63a3b3-a7aa-4683-9185-cd85f74ad553`.
  Resolve identity live if Atlassian returns a different author or owner ID.
- Engineering ADRs, especially recent pages with active comments:
  `https://example.atlassian.net/wiki/spaces/Engineering/overview`
- Release Team / Delivery context:
  `https://example.atlassian.net/wiki/spaces/Delivery/overview`

For overview URLs, resolve the space live rather than assuming its numeric ID.
For direct page URLs, parse the page ID and fetch the page directly.

## Parse a page URL and fetch the page

```ts
const url = "https://example.atlassian.net/wiki/spaces/Engineering/pages/123456789/ADR+2026-06-30+Resource+Type+Usage+Categories+and+Amenity+Templates";
const pageId = url.match(/\/pages\/(\d+)\//)?.[1];
if (!pageId) throw new Error("No Confluence page ID found in URL");

const res = await tools.atlassian_mcp.org.localatlassianmcp.getconfluencepage({
  cloudId: "example.atlassian.net",
  pageId,
});
if (!res.ok || res.data?.isError) throw new Error(JSON.stringify(res));
const page = JSON.parse(res.data.content[0].text);
```

`getconfluencepage` returns metadata such as `title`, `authorId`, `ownerId`,
`createdAt`, `version.number`, `version.authorId`, `version.createdAt`, and
`body`.

## Search broadly with Rovo

Use this for fuzzy searches like "Release Team", "resource type usage", or
"the user's blog post about X".

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.search({
  cloudId: "example.atlassian.net",
  query: "Release Team",
});
const results = JSON.parse(res.data.content[0].text).results;
```

Rovo search can return Jira and Confluence objects. For Confluence pages, IDs
may be ARIs; use `fetch` for ARIs or parse the URL/page ID and call
`getconfluencepage`.

## Search precisely with CQL

Use CQL only for Confluence-specific filters.

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.searchconfluenceusingcql({
  cloudId: "example.atlassian.net",
  cql: 'space = "Engineering" AND title ~ "ADR" ORDER BY lastmodified DESC',
  limit: 10,
});
const matches = JSON.parse(res.data.content[0].text).results;
```

Useful CQL shapes:

```ts
'space = "Delivery" AND text ~ "Release Team" ORDER BY lastmodified DESC'
'space = "Engineering" AND title ~ "ADR" ORDER BY lastmodified DESC'
'type = blogpost AND creator = currentUser() ORDER BY created DESC'
```

## Fetch comments before summarizing active pages

```ts
const [inlineRes, footerRes] = await Promise.all([
  tools.atlassian_mcp.org.localatlassianmcp.getconfluencepageinlinecomments({
    cloudId: "example.atlassian.net",
    pageId,
  }),
  tools.atlassian_mcp.org.localatlassianmcp.getconfluencepagefootercomments({
    cloudId: "example.atlassian.net",
    pageId,
  }),
]);

const inlineComments = JSON.parse(inlineRes.data.content[0].text).results;
const footerComments = JSON.parse(footerRes.data.content[0].text).results;
```

Inline comments include fields such as `body`, `createdAt`,
`resolutionStatus`, and properties containing the selected text. Fetch child
comments when a thread has replies:

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.getconfluencecommentchildren({
  cloudId: "example.atlassian.net",
  commentId: "2555478017",
});
const replies = JSON.parse(res.data.content[0].text).results;
```

## Browse spaces and pages

`getpagesinconfluencespace` takes `spaceId`, not a space key. Resolve spaces
live first when starting from an overview URL or a space key.

```ts
const spacesRes = await tools.atlassian_mcp.org.localatlassianmcp.getconfluencespaces({
  cloudId: "example.atlassian.net",
  limit: 50,
});
const spaces = JSON.parse(spacesRes.data.content[0].text).results;
const rtd = spaces.find((space) => space.key === "Delivery");

const pagesRes = await tools.atlassian_mcp.org.localatlassianmcp.getpagesinconfluencespace({
  cloudId: "example.atlassian.net",
  spaceId: rtd.id,
  limit: 25,
});
const pages = JSON.parse(pagesRes.data.content[0].text).results;
```

Fetch child pages from a known parent:

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.getconfluencepagedescendants({
  cloudId: "example.atlassian.net",
  pageId,
});
const descendants = JSON.parse(res.data.content[0].text).results;
```

## Create a personal-space page or blog post

Only write when the SkillSpec contract and SKILL.md non-negotiables pass. In
practice this means the user explicitly asked for a page or blog post in his
personal space. The create tool requires `spaceId` and `body`; include `title`
for normal published pages.

The create body must already be valid in its declared format. In particular,
an HTML body may contain only ADF-compatible block nodes at its root. Do not
use raw sentinels such as `{{CHART_01}}`, bare text, or Markdown image syntax as
root-level placeholders: Confluence can reject them before a content ID exists
for attachment upload.

For a new post whose inline attachments require the new content ID, use a
two-phase write:

1. Create the post with a valid temporary block for each intended placement,
   such as `<p><em>Chart pending: resource-test-runtime</em></p>`.
2. Upload each attachment against the returned content ID.
3. Fetch the newly created HTML. Match the normalized placeholder blocks from
   that fresh body rather than assuming Confluence preserved the input bytes.
4. Replace only those blocks with the media nodes described below, then
   dry-run, publish against a fresh snapshot, and read back.

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.createconfluencepage({
  cloudId: "example.atlassian.net",
  spaceId,
  title: "Draft title",
  body: "Markdown body...",
  parentId, // omit when creating at space root or when not applicable
});
const created = JSON.parse(res.data.content[0].text);
```

If creating a blog post or draft requires additional fields, re-resolve the
tool with `tools.search({ query: "create confluence page blog post" })` before
calling it.

## Update the user's personal-space page

Only update pages the user authored or owns in his personal space. Never update
someone else's page, team-owned pages, ADRs, Engineering pages, or Delivery / Release Team
pages. Fetch the page immediately before updating so you have the current body,
title, author/owner, and version metadata. Preserve unrelated content.

```ts
const currentRes = await tools.atlassian_mcp.org.localatlassianmcp.getconfluencepage({
  cloudId: "example.atlassian.net",
  pageId,
});
const current = JSON.parse(currentRes.data.content[0].text);

const res = await tools.atlassian_mcp.org.localatlassianmcp.updateconfluencepage({
  cloudId: "example.atlassian.net",
  pageId,
  title: current.title,
  body: nextBody,
});
const updated = JSON.parse(res.data.content[0].text);
```

### Choose a supported content width

Use the `contentWidth` field exposed by `createConfluenceContent` and
`updateConfluenceContent`; do not inject `style`, `max-width`, or wrapper HTML
that Confluence may sanitize or normalize.

- `narrow`: default for prose-heavy pages and blog posts; targets a readable
  text measure rather than an exact CSS width.
- `wide`: use when large tables, diagrams, or side-by-side content would become
  materially harder to read.
- `max`: reserve for dashboards or artifacts that explicitly need the canvas.

For mixed prose and visuals, start with `narrow` and let inline media use the
available column. A requested exact pixel or `ch` width is not supported by
this API; report that limitation instead of approximating it with CSS.

For a width-only update:

1. Fetch full current HTML and metadata; verify the user's author or owner ID.
2. Call the live format guide for `updateConfluencePage`.
3. Dry-run `updateConfluenceContent` with the current title and body unchanged,
   the fresh `snapshotToken`, and the selected `contentWidth`.
4. Fetch again, repeat the update against the fresh snapshot, then read back.
5. Verify the update response reports the requested `contentWidth`, and verify
   the readback retained the title, body, and every existing media `fileId`.

```ts
const result = await tools[updatePath]({
  cloudId: "https://example.atlassian.net",
  contentId: current.id,
  snapshotToken: current.snapshotToken,
  title: current.title,
  body: { format: "html", value: current.body.value },
  contentWidth: "narrow",
  dryRun: true,
});
```

## Upload and embed images with Rovo MCP v2

Use this branch for local files or inline images. The v1 Atlassian catalog may
support page text while lacking attachment upload; that does not prove upload
is unavailable. If the v2 integration is absent or OAuth needs repair, load
`$executor-cli` and follow its remote-MCP registration flow.

Before upload, choose and validate the delivery asset:

- Keep vector diagrams as SVG when Confluence renders them correctly.
- Convert raster charts or rasterized diagrams to WEBP. PNG may be used as a
  temporary rendering step; JPEG/PNG delivery requires an explicit
  compatibility reason.
- Inspect the file with `file` (and `identify` or `sips` when available) to
  confirm its MIME/type, pixel dimensions, and byte size. After upload, compare
  those facts with the returned attachment metadata.

1. Find the independently named v2 integration and its exact connection path:

   ```sh
   executor tools integrations
   executor tools search 'create Confluence attachment upload image' \
     --namespace atlassian_rovo_v2_preview
   ```

2. Call the connection's `discover` tool. Use only the returned operation name
   and execute-family tool; do not assume a cached schema:

   ```sh
   executor call tools.<integration>.<owner>.<connection>.discover \
     '{"query":"upload or create a Confluence attachment image file"}'
   ```

3. Call `executeWrite` with the discovered `createConfluenceAttachment`
   operation, the owning content ID, local path, and optional byte size. Parse
   its `uploadCommand` and execute that command locally without echoing or
   logging it. It contains a short-lived bearer token.

   ```json
   {
     "cloudId": "https://example.atlassian.net/wiki",
     "name": "createConfluenceAttachment",
     "inputs": {
       "contentId": "2740158473",
       "localFilePath": "/absolute/path/chart.webp",
       "fileSize": 70760,
       "comment": "Chart description"
     }
   }
   ```

4. Retain the upload response's `fileId`; the returned `id` beginning with
   `att` is attachment metadata, not the media ID used in the body. For a
   normal page or blog-post attachment, use collection
   `contentId-<contentId>`. Confirm the upload response reports the expected
   filename, byte size, and MIME type (for example `image/webp`).

5. Fetch the current content as full HTML with metadata immediately before the
   body update. Verify the user's `authorId` or `ownerId`, preserve the title and
   unrelated HTML, and retain the returned `snapshotToken`.

6. Call `getContentFormatGuide` for `updateConfluencePage`, then embed the
   media using the current guide. The v2 HTML shape at the time of writing is:

   ```html
   <figure data-type="media-single" data-layout="center" data-width="80">
     <div data-type="media" data-media-type="file"
       data-id="MEDIA_FILE_ID"
       data-collection="contentId-CONTENT_ID"
       data-alt="Accessible description"></div>
     <figcaption>Useful caption</figcaption>
   </figure>
   ```

7. Call `updateConfluenceContent` with `dryRun: true` first. On validation
   success, repeat against a freshly fetched snapshot with `dryRun: false`.
   Read the page back and verify every requested `fileId` occurs in a
   `media-single` node. An uploaded but unreferenced attachment is incomplete
   when inline placement was requested.

If a batch partially uploads or the body update fails, do not delete the
successful attachments automatically. Report their attachment IDs, filenames,
and whether they remain unreferenced so the user can retry or explicitly
authorize cleanup.

## Comment

Comments are writes. By default, do not comment on someone else's Confluence
page; draft the proposed comment in the response instead. Footer comments are
the safer format only after the SkillSpec contract and SKILL.md non-negotiables
pass.

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.createconfluencefootercomment({
  cloudId: "example.atlassian.net",
  pageId,
  body: "Comment text...",
});
const comment = JSON.parse(res.data.content[0].text);
```

Inline comments require exact selected text and match counts from the fetched
page body. If the selected text appears more than once and you cannot identify
the intended occurrence, do not guess. The tool registry describes
`inlineCommentProperties` as the selection-and-match-count object, but does not
expose the nested schema; re-resolve the tool or prefer a footer comment unless
you can validate the exact shape live.

```ts
await tools.search({
  query: "createconfluenceinlinecomment inlineCommentProperties",
});
```

For replies, provide only `parentCommentId` and `body`:

```ts
const res = await tools.atlassian_mcp.org.localatlassianmcp.createconfluenceinlinecomment({
  cloudId: "example.atlassian.net",
  parentCommentId: "2555478017",
  body: "Reply text...",
});
```
