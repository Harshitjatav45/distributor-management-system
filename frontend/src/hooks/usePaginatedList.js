import { useEffect, useRef, useState } from 'react';
import client from '../api/client';

/**
 * Drives a server-paginated DRF list endpoint ({count, next, previous, results}).
 * Resets to page 1 whenever `search` or `filters` changes; page itself is
 * left alone when only the page number changes. Re-fetches on any change.
 *
 * @param {string} basePath - API path, e.g. '/company/'
 * @param {object} options
 * @param {string} options.search - free-text search term (sent as ?search=)
 * @param {object} options.filters - extra query params, e.g. {status: 'DRAFT'}
 * @param {number} options.pageSize - optional explicit page size
 */
export default function usePaginatedList(basePath, { search = '', filters = {}, pageSize } = {}) {
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadToken, setReloadToken] = useState(0);

  const filtersKey = JSON.stringify(filters);
  const resetRef = useRef({ search, filtersKey });

  // Reset to page 1 when search/filters change (not on plain page changes).
  useEffect(() => {
    if (resetRef.current.search !== search || resetRef.current.filtersKey !== filtersKey) {
      resetRef.current = { search, filtersKey };
      setPage(1);
    }
  }, [search, filtersKey]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = { page, ...filters };
    if (search) params.search = search;
    if (pageSize) params.page_size = pageSize;

    client.get(basePath, { params })
      .then((resp) => {
        if (cancelled) return;
        setRows(resp.data.results);
        setCount(resp.data.count);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [basePath, page, search, filtersKey, pageSize, reloadToken]);

  const effectivePageSize = pageSize || 25;
  const totalPages = Math.max(1, Math.ceil(count / effectivePageSize));

  return {
    rows, count, loading, error, page, setPage, totalPages,
    reload: () => setReloadToken((t) => t + 1),
  };
}
