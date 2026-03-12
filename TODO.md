# TODO

## Photo upload & management (posts app)

### Setup
- Vendor `@alpinejs/focus` plugin into `static/vendor/` and load it in `base.html`

### Create view
- Custom multi-file upload widget (Alpine.js): `<input type="file" multiple>` with
  client-side preview (URL.createObjectURL) and per-file remove before upload
- View handles `request.FILES.getlist("photos")`, creates Photo instances,
  sets first uploaded photo as cover

### Edit view
- Show existing photos as thumbnails (sorl-thumbnail)
- Remove individual photo: HTMX DELETE per photo
- Set cover photo: HTMX action per photo (clears existing cover, sets new one)
- Add more photos: same multi-file upload widget as create view

### Detail view
- Photo grid using `grid.html` + sorl-thumbnail thumbnails
- Clicking a thumbnail opens a full-screen Alpine.js carousel modal
  - Focus-trapped via `@alpinejs/focus` (`x-trap`)
  - Keyboard navigation (arrow keys, Escape to close)
  - Swipe support

### List view (and future post list views)
- Custom `PostQuerySet` with `with_cover_photo()` method
  - Annotates queryset with cover photo file path via `Subquery` on `Photo` where `is_cover=True`
- Use annotation in list template to render cover thumbnail per post
