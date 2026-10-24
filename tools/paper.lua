-- Pandoc filter for paper pages. Runs after --citeproc.
-- Adds the "of special/outstanding interest" annotations from the paper's
-- `annotations` metadata to the matching entries in the reference list.

local labels = {
  special = 'Of special interest',
  outstanding = 'Of outstanding interest',
}

function Pandoc(doc)
  local annotations = doc.meta.annotations or {}
  doc.blocks = doc.blocks:walk({
    Div = function(div)
      local key = div.identifier:match('^ref%-(.+)$')
      local note = key and annotations[key]
      if not note then return nil end
      local level = pandoc.utils.stringify(note.level)
      local inlines = pandoc.List({ pandoc.Strong(labels[level] .. '.'), pandoc.Space() })
      inlines:extend(note.text)
      div.classes:insert('annotated')
      div.content:insert(pandoc.Div({ pandoc.Para(inlines) }, { class = 'annotation ' .. level }))
      return div
    end,
  })
  doc.meta.annotations = nil
  return doc
end
