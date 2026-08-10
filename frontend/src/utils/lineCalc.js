export function round2(n) {
  return Math.round((Number(n) + Number.EPSILON) * 100) / 100;
}

// Standard line computation shared by Purchase and Sales items: gross ->
// item discount -> taxable amount -> GST -> line total. Backend requires
// these fields be sent explicitly (no server-side auto-calculation exists
// for taxable_amount/gst_amount/line_total), so the frontend computes them
// once here and both modules reuse the exact same formula.
export function computeLine({ quantity, rate, discount_percentage, gst_percentage }) {
  const qty = Number(quantity) || 0;
  const r = Number(rate) || 0;
  const discPct = Number(discount_percentage) || 0;
  const gstPct = Number(gst_percentage) || 0;

  const gross = qty * r;
  const discount_amount = round2(gross * discPct / 100);
  const taxable_amount = round2(gross - discount_amount);
  const gst_amount = round2(taxable_amount * gstPct / 100);
  const line_total = round2(taxable_amount + gst_amount);

  return { discount_amount, taxable_amount, gst_amount, line_total };
}

export function aggregateHeaderTotals(items, roundOff = 0) {
  const total_amount = round2(items.reduce((s, i) => s + Number(i.taxable_amount || 0), 0));
  const discount_amount = round2(items.reduce((s, i) => s + Number(i.discount_amount || 0), 0));
  const gst_amount = round2(items.reduce((s, i) => s + Number(i.gst_amount || 0), 0));
  const grand_total = round2(total_amount + gst_amount + Number(roundOff || 0));
  return { total_amount, discount_amount, gst_amount, grand_total };
}
