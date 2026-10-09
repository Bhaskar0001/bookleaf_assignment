import React, { useState } from 'react';
import { Paperclip, FileText, Download, Eye, X, Image as ImageIcon } from 'lucide-react';

interface AttachmentItem {
  filename: string;
  dataUrl?: string;
  isImage: boolean;
}

interface AttachmentViewerProps {
  content: string;
  className?: string;
}

export const AttachmentViewer: React.FC<AttachmentViewerProps> = ({ content }) => {
  const [lightboxImage, setLightboxImage] = useState<{ src: string; name: string } | null>(null);

  if (!content) return null;

  // Regex to extract [Attachment: filename](dataUrl) or [Attachment: filename]
  const attachmentRegex = /\[Attachment:\s*([^\]]+)\](?:\(([^)]+)\))?/gi;
  const attachments: AttachmentItem[] = [];

  let match;
  while ((match = attachmentRegex.exec(content)) !== null) {
    const filename = match[1].trim();
    const dataUrl = match[2]?.trim();
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const isImage = (dataUrl && dataUrl.startsWith('data:image/')) ||
      ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'].includes(ext);

    attachments.push({
      filename,
      dataUrl,
      isImage: Boolean(isImage),
    });
  }

  // Strip out attachment tokens from the body text
  const cleanedText = content.replace(attachmentRegex, '').trim();

  return (
    <div>
      {/* Primary message / description text */}
      {cleanedText && (
        <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5, marginBottom: attachments.length > 0 ? '0.85rem' : 0 }}>
          {cleanedText}
        </p>
      )}

      {/* Render Attachments section */}
      {attachments.length > 0 && (
        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Paperclip size={13} />
            <span>Attached Evidence ({attachments.length})</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '0.65rem' }}>
            {attachments.map((att, idx) => {
              if (att.isImage && att.dataUrl) {
                return (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      background: '#ffffff',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                    }}
                  >
                    {/* Thumbnail preview */}
                    <div
                      onClick={() => setLightboxImage({ src: att.dataUrl!, name: att.filename })}
                      style={{
                        position: 'relative',
                        height: '140px',
                        background: '#f8fafc',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        overflow: 'hidden',
                      }}
                      title="Click to expand"
                    >
                      <img
                        src={att.dataUrl}
                        alt={att.filename}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <div
                        style={{
                          position: 'absolute',
                          inset: 0,
                          background: 'rgba(15, 23, 42, 0.35)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          opacity: 0,
                          transition: 'opacity 0.15s ease',
                          color: '#ffffff',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          gap: '0.4rem',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                        onMouseLeave={(e) => (e.currentTarget.style.opacity = '0')}
                      >
                        <Eye size={16} /> View Image
                      </div>
                    </div>

                    {/* Image Footer with actions */}
                    <div style={{ padding: '0.5rem 0.65rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#ffffff', borderTop: '1px solid #f1f5f9' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#1e293b',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: '140px',
                        }}
                        title={att.filename}
                      >
                        {att.filename}
                      </span>
                      <a
                        href={att.dataUrl}
                        download={att.filename}
                        style={{
                          fontSize: '0.75rem',
                          color: '#2563eb',
                          textDecoration: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          fontWeight: 600,
                        }}
                      >
                        <Download size={13} /> Download
                      </a>
                    </div>
                  </div>
                );
              }

              if (att.dataUrl) {
                // Non-image with real data URL (PDF, document, text file)
                return (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '0.65rem 0.85rem',
                      background: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.5rem',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
                      <div style={{ background: '#eff6ff', color: '#2563eb', padding: '0.4rem', borderRadius: '6px' }}>
                        <FileText size={16} />
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            color: '#1e293b',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: '140px',
                          }}
                          title={att.filename}
                        >
                          {att.filename}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Attached Document</div>
                      </div>
                    </div>
                    <a
                      href={att.dataUrl}
                      download={att.filename}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '0.75rem', padding: '0.3rem 0.55rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', textDecoration: 'none' }}
                    >
                      <Download size={12} /> Save
                    </a>
                  </div>
                );
              }

              // Text-only reference without stored data URL (from earlier tests)
              return (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '0.5rem 0.75rem',
                    background: '#f8fafc',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.75rem',
                    color: '#475569',
                  }}
                >
                  {att.isImage ? <ImageIcon size={14} color="#64748b" /> : <FileText size={14} color="#64748b" />}
                  <span style={{ fontWeight: 600, color: '#334155' }}>{att.filename}</span>
                  <span style={{ color: '#94a3b8', fontSize: '0.7rem' }}>(Referenced in ticket)</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Lightbox Modal for Full-Size Image Preview */}
      {lightboxImage && (
        <div
          onClick={() => setLightboxImage(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.85)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'relative',
              maxWidth: '90vw',
              maxHeight: '90vh',
              background: '#ffffff',
              borderRadius: '10px',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>{lightboxImage.name}</span>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <a
                  href={lightboxImage.src}
                  download={lightboxImage.name}
                  className="btn btn-primary btn-sm"
                  style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem' }}
                >
                  <Download size={13} /> Download
                </a>
                <button
                  onClick={() => setLightboxImage(null)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: '0.2rem' }}
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <img
              src={lightboxImage.src}
              alt={lightboxImage.name}
              style={{ maxWidth: '85vw', maxHeight: '75vh', objectFit: 'contain', borderRadius: '6px' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
