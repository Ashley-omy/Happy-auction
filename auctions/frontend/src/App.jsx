import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${normalizedPath}`
}

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split('; ') : []
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`))
  return match ? decodeURIComponent(match.split('=').slice(1).join('=')) : null
}

async function ensureCsrfCookie() {
  if (getCookie('csrftoken')) {
    return
  }

  await fetch(buildApiUrl('/auth/csrf/'), {
    credentials: 'include',
  })
}

async function apiRequest(path, options = {}) {
  const config = {
    credentials: 'include',
    headers: {},
    ...options,
  }

  if (config.body && !(config.body instanceof FormData)) {
    config.headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    }
  }

  if (config.method && config.method !== 'GET' && config.method !== 'HEAD') {
    await ensureCsrfCookie()
    config.headers = {
      'X-CSRFToken': getCookie('csrftoken') || '',
      ...config.headers,
    }
  }

  const response = await fetch(buildApiUrl(path), config)
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof data === 'string'
        ? data
        : data.error ||
          Object.values(data).flat().join(' ') ||
          'Something went wrong.'
    throw new Error(message)
  }

  return data
}

function navigate(pathname) {
  window.history.pushState({}, '', pathname)
  window.dispatchEvent(new Event('app:navigate'))
}

function usePathname() {
  const [pathname, setPathname] = useState(window.location.pathname)

  useEffect(() => {
    const syncPath = () => setPathname(window.location.pathname)
    window.addEventListener('popstate', syncPath)
    window.addEventListener('app:navigate', syncPath)
    return () => {
      window.removeEventListener('popstate', syncPath)
      window.removeEventListener('app:navigate', syncPath)
    }
  }, [])

  return pathname
}

function Link({ to, className, children }) {
  return (
    <a
      href={to}
      className={className}
      onClick={(event) => {
        if (
          event.defaultPrevented ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        ) {
          return
        }
        event.preventDefault()
        navigate(to)
      }}
    >
      {children}
    </a>
  )
}

function formatMoney(value) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

function formatDate(value) {
  if (!value) {
    return 'Unknown date'
  }

  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'long',
    timeStyle: 'short',
  }).format(new Date(value))
}

function parseRoute(pathname) {
  if (pathname === '/') {
    return { page: 'home' }
  }
  if (pathname === '/closed') {
    return { page: 'closed' }
  }
  if (pathname === '/new') {
    return { page: 'new' }
  }
  if (pathname === '/watchlist') {
    return { page: 'watchlist' }
  }
  if (pathname === '/my-auctions') {
    return { page: 'my-auctions' }
  }
  if (pathname === '/categories') {
    return { page: 'categories' }
  }
  if (pathname === '/login') {
    return { page: 'login' }
  }
  if (pathname === '/register') {
    return { page: 'register' }
  }
  if (pathname.startsWith('/auction/')) {
    return { page: 'auction', auctionId: pathname.split('/')[2] }
  }
  if (pathname.startsWith('/categories/')) {
    return {
      page: 'category-listings',
      categoryName: decodeURIComponent(pathname.replace('/categories/', '')),
    }
  }
  return { page: 'not-found' }
}

function App() {
  const pathname = usePathname()
  const route = parseRoute(pathname)
  const [auth, setAuth] = useState({
    authenticated: false,
    user: null,
    loading: true,
  })

  useEffect(() => {
    let active = true

    async function loadAuth() {
      try {
        const data = await apiRequest('/auth/me/')
        if (active) {
          setAuth({
            authenticated: data.authenticated,
            user: data.user,
            loading: false,
          })
        }
      } catch {
        if (active) {
          setAuth({
            authenticated: false,
            user: null,
            loading: false,
          })
        }
      }
    }

    loadAuth()
    return () => {
      active = false
    }
  }, [])

  async function refreshAuth() {
    const data = await apiRequest('/auth/me/')
    setAuth({
      authenticated: data.authenticated,
      user: data.user,
      loading: false,
    })
  }

  async function handleLogout() {
    await apiRequest('/auth/logout/', {
      method: 'POST',
    })
    await refreshAuth()
    navigate('/')
  }

  return (
    <div className="app-shell">
      <AppHeader auth={auth} onLogout={handleLogout} />
      <main className="page-shell">
        <RouteView route={route} auth={auth} refreshAuth={refreshAuth} />
      </main>
    </div>
  )
}

function AppHeader({ auth, onLogout }) {
  return (
    <header className="masthead">
      <div className="masthead__intro">
        <p className="eyebrow">Online Marketplace</p>
        <Link to="/" className="brand">
          Happy Auctions
        </Link>
        <p className="tagline">
          Browse active bids, follow favorites, and close your own listings.
        </p>
      </div>
      {auth.authenticated && !auth.loading ? (
        <div className="status-card">
          <strong className="status-card__user">{auth.user.username}</strong>
        </div>
      ) : null}
      <nav className="main-nav">
        <Link to="/" className="main-nav__link btn btn-outline-success rounded-pill">
          Active
        </Link>
        <Link to="/closed" className="main-nav__link btn btn-outline-success rounded-pill">
          Closed
        </Link>
        <Link to="/categories" className="main-nav__link btn btn-outline-success rounded-pill">
          Categories
        </Link>
        {auth.authenticated ? (
          <>
            <Link to="/new" className="main-nav__link btn btn-outline-success rounded-pill">
              New Auction
            </Link>
            <Link to="/watchlist" className="main-nav__link btn btn-outline-success rounded-pill">
              Watchlist
            </Link>
            <Link to="/my-auctions" className="main-nav__link btn btn-outline-success rounded-pill">
              My Auctions
            </Link>
            <button
              type="button"
              className="main-nav__button btn btn-outline-danger rounded-pill"
              onClick={onLogout}
            >
              Log Out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="main-nav__link btn btn-outline-success rounded-pill">
              Log In
            </Link>
            <Link to="/register" className="main-nav__link btn btn-success rounded-pill">
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}

function RouteView({ route, auth, refreshAuth }) {
  switch (route.page) {
    case 'home':
      return (
        <ListingPage
          title="Active Listings"
          description="Fresh auctions with live pricing."
          query="?status=active"
          emptyMessage="No active listings available."
          auth={auth}
        />
      )
    case 'closed':
      return (
        <ListingPage
          title="Closed Auctions"
          description="Finished auctions with final prices and winners."
          query="?status=closed"
          emptyMessage="There are no closed listings yet."
          auth={auth}
        />
      )
    case 'watchlist':
      return auth.authenticated ? (
        <ListingPage
          title="Watchlist"
          description="Listings you bookmarked for a closer look."
          query="?watchlist=me&status=all"
          emptyMessage="Your watchlist is empty."
          auth={auth}
        />
      ) : (
        <AuthRequiredCard />
      )
    case 'my-auctions':
      return auth.authenticated ? (
        <ListingPage
          title="My Auctions"
          description="Everything you created, including active and closed listings."
          query="?owner=me&status=all"
          emptyMessage="You haven't created any auctions yet."
          auth={auth}
        />
      ) : (
        <AuthRequiredCard />
      )
    case 'categories':
      return <CategoriesPage />
    case 'category-listings':
      return (
        <ListingPage
          title={`Category: ${route.categoryName}`}
          description="Listings filtered down to a single category."
          query={`?category=${encodeURIComponent(route.categoryName)}&status=active`}
          emptyMessage="No active listings in this category."
          auth={auth}
        />
      )
    case 'auction':
      return <AuctionDetailPage auctionId={route.auctionId} auth={auth} />
    case 'new':
      return auth.authenticated ? <CreateAuctionPage /> : <AuthRequiredCard />
    case 'login':
      return <LoginPage refreshAuth={refreshAuth} />
    case 'register':
      return <RegisterPage refreshAuth={refreshAuth} />
    default:
      return <NotFoundPage />
  }
}

function AuthRequiredCard() {
  return (
    <section className="panel panel--compact">
      <h1>Sign in required</h1>
      <p className="panel__lead">
        This page uses your account data, so you’ll need to log in first.
      </p>
      <div className="stack-row">
        <Link to="/login" className="button button--primary btn btn-success rounded-pill">
          Log In
        </Link>
        <Link to="/register" className="button button--ghost btn btn-outline-success rounded-pill">
          Create Account
        </Link>
      </div>
    </section>
  )
}

function ListingPage({ title, description, query, emptyMessage, auth }) {
  const [state, setState] = useState({
    loading: true,
    auctions: [],
    error: '',
  })

  useEffect(() => {
    let active = true

    async function loadAuctions() {
      try {
        const auctions = await apiRequest(`/auctions/${query}`)
        if (active) {
          setState({
            loading: false,
            auctions,
            error: '',
          })
        }
      } catch (error) {
        if (active) {
          setState({
            loading: false,
            auctions: [],
            error: error.message,
          })
        }
      }
    }

    loadAuctions()
    return () => {
      active = false
    }
  }, [query])

  async function handleWatchlistToggle(auctionId) {
    try {
      const data = await apiRequest('/watchlist/toggle/', {
        method: 'POST',
        body: JSON.stringify({ auction_id: auctionId }),
      })
      setState((current) => ({
        ...current,
        auctions: current.auctions.map((auction) =>
          auction.id === auctionId
            ? { ...auction, in_watchlist: data.in_watchlist }
            : auction,
        ),
      }))
    } catch (error) {
      window.alert(error.message)
    }
  }

  return (
    <section className="panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Browse</p>
          <h1>{title}</h1>
          <p className="panel__lead">{description}</p>
        </div>
      </div>

      {state.loading ? <p>Loading listings...</p> : null}
      {state.error ? <p className="notice notice--error">{state.error}</p> : null}

      {!state.loading && !state.error && state.auctions.length === 0 ? (
        <p>{emptyMessage}</p>
      ) : null}

      <div className="auction-grid">
        {state.auctions.map((auction) => (
          <AuctionCard
            key={auction.id}
            auction={auction}
            auth={auth}
            onToggleWatchlist={handleWatchlistToggle}
          />
        ))}
      </div>
    </section>
  )
}

function AuctionCard({ auction, auth, onToggleWatchlist }) {
  const winnerId = auction.winner ?? null
  const didWin = auth.user && winnerId && auth.user.id === winnerId

  return (
    <article className="auction-card">
      <div className="auction-card__media">
        {auction.image_url ? (
          <img src={auction.image_url} alt={auction.title} />
        ) : (
          <div className="auction-card__placeholder">No image</div>
        )}
      </div>
      <div className="auction-card__body">
        <div className="auction-card__topline">
          <span className={`pill ${auction.is_active ? 'pill--live' : 'pill--closed'}`}>
            {auction.is_active ? 'Live' : 'Closed'}
          </span>
          <span className="auction-card__category">
            {auction.category?.name || 'Uncategorized'}
          </span>
        </div>
        <h2>{auction.title}</h2>
        <p className="auction-card__description">{auction.description}</p>
        <dl className="facts">
          <div>
            <dt>Current</dt>
            <dd>{formatMoney(auction.current_price)}</dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>{auction.owner_username}</dd>
          </div>
        </dl>
        {didWin ? <p className="notice notice--success">You won this auction.</p> : null}
        <div className="stack-row">
          <Link
            to={`/auction/${auction.id}`}
            className="button button--primary btn btn-success rounded-pill"
          >
            View Auction
          </Link>
          {auth.authenticated ? (
            <button
              type="button"
              className="button button--ghost btn btn-outline-success rounded-pill"
              onClick={() => onToggleWatchlist(auction.id)}
            >
              {auction.in_watchlist ? 'Remove Watchlist' : 'Add Watchlist'}
            </button>
          ) : null}
        </div>
      </div>
    </article>
  )
}

function AuctionDetailPage({ auctionId, auth }) {
  const [state, setState] = useState({
    loading: true,
    auction: null,
    error: '',
    bidAmount: '',
    comment: '',
    message: '',
  })

  useEffect(() => {
    let active = true

    async function loadAuction() {
      try {
        const auction = await apiRequest(`/auctions/${auctionId}/`)
        if (active) {
          setState((current) => ({
            ...current,
            loading: false,
            auction,
            error: '',
            message: '',
          }))
        }
      } catch (error) {
        if (active) {
          setState((current) => ({
            ...current,
            loading: false,
            error: error.message,
          }))
        }
      }
    }

    loadAuction()
    return () => {
      active = false
    }
  }, [auctionId])

  async function refreshAuction(message = '') {
    const auction = await apiRequest(`/auctions/${auctionId}/`)
    setState((current) => ({
      ...current,
      auction,
      loading: false,
      error: '',
      message,
    }))
  }

  async function handleBidSubmit(event) {
    event.preventDefault()
    try {
      await apiRequest(`/auctions/${auctionId}/bid/`, {
        method: 'POST',
        body: JSON.stringify({ bid_amount: state.bidAmount }),
      })
      setState((current) => ({ ...current, bidAmount: '' }))
      await refreshAuction('Bid placed successfully.')
    } catch (error) {
      setState((current) => ({ ...current, message: error.message }))
    }
  }

  async function handleCommentSubmit(event) {
    event.preventDefault()
    try {
      await apiRequest(`/auctions/${auctionId}/comment/`, {
        method: 'POST',
        body: JSON.stringify({ content: state.comment }),
      })
      setState((current) => ({ ...current, comment: '' }))
      await refreshAuction('Comment added.')
    } catch (error) {
      setState((current) => ({ ...current, message: error.message }))
    }
  }

  async function handleWatchlistToggle() {
    try {
      await apiRequest('/watchlist/toggle/', {
        method: 'POST',
        body: JSON.stringify({ auction_id: auctionId }),
      })
      await refreshAuction()
    } catch (error) {
      setState((current) => ({ ...current, message: error.message }))
    }
  }

  async function handleCloseAuction() {
    try {
      const auction = await apiRequest(`/auctions/${auctionId}/close/`, {
        method: 'POST',
      })
      setState((current) => ({
        ...current,
        auction,
        message: 'Auction closed.',
      }))
    } catch (error) {
      setState((current) => ({ ...current, message: error.message }))
    }
  }

  if (state.loading) {
    return <section className="panel"><p>Loading auction...</p></section>
  }

  if (state.error) {
    return (
      <section className="panel">
        <p className="notice notice--error">{state.error}</p>
      </section>
    )
  }

  const { auction } = state
  const isOwner = auth.user && auction.owner === auth.user.id
  const didWin = auth.user && auction.winner === auth.user.id

  return (
    <section className="panel">
      <div className="detail-hero">
        <div className="detail-hero__copy">
          <p className="eyebrow">Auction Detail</p>
          <h1>{auction.title}</h1>
          <p className="panel__lead">{auction.description}</p>
          <div className="stack-row stack-row--wrap">
            <span className={`pill ${auction.is_active ? 'pill--live' : 'pill--closed'}`}>
              {auction.is_active ? 'Live auction' : 'Closed auction'}
            </span>
            <span className="pill pill--soft">
              {auction.category?.name || 'No category'}
            </span>
            <span className="pill pill--soft">By {auction.owner_username}</span>
          </div>
        </div>
        <div className="detail-hero__media">
          {auction.image_url ? (
            <img src={auction.image_url} alt={auction.title} />
          ) : (
            <div className="auction-card__placeholder">No image</div>
          )}
        </div>
      </div>

      <div className="detail-layout">
        <section className="detail-panel">
          <h2>Bid Snapshot</h2>
          <dl className="facts">
            <div>
              <dt>Starting bid</dt>
              <dd>{formatMoney(auction.starting_bid)}</dd>
            </div>
            <div>
              <dt>Current price</dt>
              <dd>{formatMoney(auction.current_price)}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatDate(auction.created_at)}</dd>
            </div>
            <div>
              <dt>Closed</dt>
              <dd>{auction.closed_at ? formatDate(auction.closed_at) : 'Still open'}</dd>
            </div>
          </dl>
          {didWin ? <p className="notice notice--success">You won this auction.</p> : null}
          {state.message ? <p className="notice notice--info">{state.message}</p> : null}

          {auth.authenticated ? (
            <div className="stack-row stack-row--wrap">
              <button
                type="button"
                className="button button--ghost btn btn-outline-success rounded-pill"
                onClick={handleWatchlistToggle}
              >
                {auction.in_watchlist ? 'Remove Watchlist' : 'Add Watchlist'}
              </button>
              {isOwner && auction.is_active ? (
                <button
                  type="button"
                  className="button button--danger btn btn-outline-danger rounded-pill"
                  onClick={handleCloseAuction}
                >
                  Close Auction
                </button>
              ) : null}
            </div>
          ) : (
            <p>Log in to bid, comment, or manage your watchlist.</p>
          )}

          {auth.authenticated && auction.is_active && !isOwner ? (
            <form className="form-card" onSubmit={handleBidSubmit}>
              <h3>Place a bid</h3>
              <label className="field">
                <span>Your bid</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={state.bidAmount}
                  onChange={(event) =>
                    setState((current) => ({
                      ...current,
                      bidAmount: event.target.value,
                    }))
                  }
                  required
                />
              </label>
              <button type="submit" className="button button--primary btn btn-success rounded-pill">
                Submit Bid
              </button>
            </form>
          ) : null}
        </section>

        <section className="detail-panel">
          <h2>Comments</h2>
          <div className="comment-list">
            {auction.comments.length === 0 ? (
              <p>No comments yet.</p>
            ) : (
              auction.comments.map((comment) => (
                <article key={comment.id} className="comment-card">
                  <strong>{comment.commenter_username}</strong>
                  <p>{comment.content}</p>
                  <span>{formatDate(comment.created_at)}</span>
                </article>
              ))
            )}
          </div>

          {auth.authenticated ? (
            <form className="form-card" onSubmit={handleCommentSubmit}>
              <h3>Add a comment</h3>
              <label className="field">
                <span>Comment</span>
                <textarea
                  value={state.comment}
                  onChange={(event) =>
                    setState((current) => ({
                      ...current,
                      comment: event.target.value,
                    }))
                  }
                  required
                />
              </label>
              <button type="submit" className="button button--primary btn btn-success rounded-pill">
                Post Comment
              </button>
            </form>
          ) : null}
        </section>
      </div>
    </section>
  )
}

function CreateAuctionPage() {
  const [form, setForm] = useState({
    title: '',
    description: '',
    starting_bid: '',
    category: '',
  })
  const [imageFile, setImageFile] = useState(null)
  const [categories, setCategories] = useState([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true

    async function loadCategories() {
      try {
        const data = await apiRequest('/categories/')
        if (active) {
          setCategories(data)
        }
      } catch (error) {
        if (active) {
          setMessage(error.message)
        }
      }
    }

    loadCategories()
    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      const payload = new FormData()
      payload.append('title', form.title)
      payload.append('description', form.description)
      payload.append('starting_bid', form.starting_bid)
      if (form.category) {
        payload.append('category', form.category)
      }
      if (imageFile) {
        payload.append('image_url', imageFile)
      }
      const auction = await apiRequest('/auctions/', {
        method: 'POST',
        body: payload,
      })
      navigate(`/auction/${auction.id}`)
    } catch (error) {
      setMessage(error.message)
    }
  }

  return (
    <section className="panel">
      <p className="eyebrow">Create</p>
      <h1>Launch a new auction</h1>
      <p className="panel__lead">Create a new auction listing.</p>
      {message ? <p className="notice notice--error">{message}</p> : null}
      <form className="form-card form-card--centered" onSubmit={handleSubmit}>
        <label className="field">
          <span>Title</span>
          <input
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            required
          />
        </label>
        <label className="field">
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
            required
          />
        </label>
        <label className="field">
          <span>Starting bid &#40;$&#41;</span>
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.starting_bid}
            onChange={(event) =>
              setForm({ ...form, starting_bid: event.target.value })
            }
            required
          />
        </label>
        <label className="field">
          <span>Image</span>
          <input
            type="file"
            accept="image/*"
            onChange={(event) => setImageFile(event.target.files?.[0] || null)}
          />
        </label>
        <label className="field">
          <span>Category</span>
          <select
            value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
          >
            <option value="">No category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="button button--primary btn btn-success rounded-pill">
          Create Auction
        </button>
      </form>
    </section>
  )
}

function CategoriesPage() {
  const [state, setState] = useState({
    loading: true,
    categories: [],
    error: '',
  })

  useEffect(() => {
    let active = true

    async function loadCategories() {
      try {
        const categories = await apiRequest('/categories/')
        if (active) {
          setState({
            loading: false,
            categories,
            error: '',
          })
        }
      } catch (error) {
        if (active) {
          setState({
            loading: false,
            categories: [],
            error: error.message,
          })
        }
      }
    }

    loadCategories()
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="panel panel--compact">
      <p className="eyebrow">Explore</p>
      <h1>Categories</h1>
      <p className="panel__lead">
        Jump directly into the kind of auction you want to browse.
      </p>
      {state.loading ? <p>Loading categories...</p> : null}
      {state.error ? <p className="notice notice--error">{state.error}</p> : null}
      <div className="category-cloud">
        {state.categories.map((category) => (
          <Link
            key={category.id}
            to={`/categories/${encodeURIComponent(category.name)}`}
            className="category-chip btn btn-outline-success rounded-pill"
          >
            {category.name}
          </Link>
        ))}
      </div>
    </section>
  )
}

function LoginPage({ refreshAuth }) {
  return (
    <AuthForm
      title="Log in"
      lead="Use your account to place bids and manage listings."
      submitLabel="Log In"
      fields={[
        { name: 'username', label: 'Username', type: 'text' },
        { name: 'password', label: 'Password', type: 'password' },
      ]}
      onSubmit={async (values) => {
        await apiRequest('/auth/login/', {
          method: 'POST',
          body: JSON.stringify(values),
        })
        await refreshAuth()
        navigate('/')
      }}
      footer={
        <p>
          Need an account? <Link to="/register" className="inline-link">Register here</Link>.
        </p>
      }
    />
  )
}

function RegisterPage({ refreshAuth }) {
  return (
    <AuthForm
      title="Register"
      lead="Create an account to bid, comment, save watchlists, and manage your own listings."
      submitLabel="Create Account"
      fields={[
        { name: 'username', label: 'Username', type: 'text' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'password', label: 'Password', type: 'password' },
        {
          name: 'confirmation',
          label: 'Confirm Password',
          type: 'password',
        },
      ]}
      onSubmit={async (values) => {
        await apiRequest('/auth/register/', {
          method: 'POST',
          body: JSON.stringify(values),
        })
        await refreshAuth()
        navigate('/')
      }}
      footer={
        <p>
          Already registered? <Link to="/login" className="inline-link">Log in</Link>.
        </p>
      }
    />
  )
}

function AuthForm({ title, lead, submitLabel, fields, onSubmit, footer }) {
  const initialState = fields.reduce((values, field) => {
    values[field.name] = ''
    return values
  }, {})

  const [values, setValues] = useState(initialState)
  const [message, setMessage] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      await onSubmit(values)
    } catch (error) {
      setMessage(error.message)
    }
  }

  return (
    <section className="panel panel--compact">
      <p className="eyebrow">Account</p>
      <h1>{title}</h1>
      <p className="panel__lead">{lead}</p>
      {message ? <p className="notice notice--error">{message}</p> : null}
      <form className="form-card" onSubmit={handleSubmit}>
        {fields.map((field) => (
          <label key={field.name} className="field">
            <span>{field.label}</span>
            <input
              type={field.type}
              value={values[field.name]}
              onChange={(event) =>
                setValues({ ...values, [field.name]: event.target.value })
              }
              required={field.name !== 'email'}
            />
          </label>
        ))}
        <button type="submit" className="button button--primary btn btn-success rounded-pill">
          {submitLabel}
        </button>
      </form>
      <div className="auth-footer">{footer}</div>
    </section>
  )
}

function NotFoundPage() {
  return (
    <section className="panel panel--compact">
      <h1>Page not found</h1>
      <p className="panel__lead">The page you requested could not be found.</p>
      <Link to="/" className="button button--primary btn btn-success rounded-pill">
        Back to auctions
      </Link>
    </section>
  )
}

export default App
