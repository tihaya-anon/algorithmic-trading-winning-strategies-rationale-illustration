local function has_class(classes, class_name)
  for _, class in ipairs(classes) do
    if class == class_name then
      return true
    end
  end

  return false
end

function Div(el)
  if FORMAT:match("revealjs") and has_class(el.classes, "notes") then
    return {}
  end
end

function Meta(meta)
  if FORMAT:match("revealjs") then
    meta.notes = nil
    return meta
  end
end
