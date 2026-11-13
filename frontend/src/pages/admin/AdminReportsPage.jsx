import React from 'react';
import { FileText, Download, Filter, Calendar } from 'lucide-react';

export default function AdminReportsPage() {
  const reports = [
    { title: 'Tournament Summary Report', desc: 'Aggregated match results, points table, and awards', type: 'PDF' },
    { title: 'Ball-by-Ball Match Log', desc: 'Complete delivery-by-delivery event export with timestamp & GPS', type: 'CSV' },
    { title: 'Player Performance Audit', desc: 'Batting strike rates, bowling economy, and boundary ratios', type: 'Excel' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-500" />
            <span>Reports & Exports</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Generate and export official tournament scorecards, audit logs, and analytics
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {reports.map((report, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card flex flex-col justify-between"
          >
            <div>
              <div className="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-3">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">{report.title}</h3>
              <p className="text-xs text-slate-500 mt-1">{report.desc}</p>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                {report.type}
              </span>
              <button className="inline-flex items-center gap-1 text-xs font-bold text-emerald-500 hover:text-emerald-600 transition">
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

