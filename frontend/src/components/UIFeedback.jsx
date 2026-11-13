import React from 'react';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';

export function LoadingSkeleton({ rows = 3, type = 'card' }) {
  if (type === 'table') {
    return (
      <div className="w-full space-y-3 animate-pulse p-4">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-xl w-full" />
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-12 bg-slate-100 dark:bg-slate-850/60 rounded-xl w-full" />
        ))}
      </div>
    );
  }

  if (type === 'list') {
    return (
      <div className="space-y-3 animate-pulse">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-20 bg-slate-100 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 flex items-center justify-between"
          >
            <div className="space-y-2 w-1/2">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
            </div>
            <div className="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded-xl" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
            <div className="h-5 w-14 bg-slate-200 dark:bg-slate-700 rounded-full" />
          </div>
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
          <div className="h-10 bg-slate-100 dark:bg-slate-800 rounded-xl" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  title = 'No records found',
  description = 'There are no items matching your criteria at this moment.',
  icon: Icon = Inbox,
  actionLabel,
  onAction,
}) {
  return (
    <div className="p-10 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card text-center my-6">
      <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-500 mx-auto mb-3 flex items-center justify-center">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold shadow-sm transition"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function ErrorState({
  message = 'An error occurred while loading data.',
  onRetry,
}) {
  return (
    <div className="p-6 rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-center my-6">
      <div className="w-10 h-10 rounded-xl bg-red-500/10 text-red-500 mx-auto mb-2 flex items-center justify-center">
        <AlertCircle className="w-5 h-5" />
      </div>
      <h3 className="text-sm font-bold text-red-700 dark:text-red-400">Failed to load content</h3>
      <p className="text-xs text-red-600 dark:text-red-300 mt-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-semibold shadow-sm transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
}
