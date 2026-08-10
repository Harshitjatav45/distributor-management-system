import MasterDataPage from './MasterDataPage';

const UNIT_CHOICES = ['PCS', 'KG', 'TON', 'METER', 'FEET', 'BUNDLE', 'NOS', 'BOX', 'SET', 'PKT'].map((u) => ({ value: u, label: u }));

const fields = [
  { name: 'material_name', label: 'Material Name', type: 'text', required: true },
  { name: 'material_code', label: 'Material Code', type: 'text', required: true },
  { name: 'company', label: 'Company', type: 'select', required: true, optionsUrl: '/company/', optionLabel: (c) => c.company_name },
  { name: 'category', label: 'Category', type: 'select', required: true, optionsUrl: '/category/', optionLabel: (c) => c.category_name },
  { name: 'unit', label: 'Unit', type: 'select', choices: UNIT_CHOICES },
  { name: 'brand', label: 'Brand', type: 'text' },
  { name: 'grade', label: 'Grade', type: 'text' },
  { name: 'size', label: 'Size', type: 'text' },
  { name: 'hsn_code', label: 'HSN Code', type: 'text' },
  { name: 'barcode', label: 'Barcode', type: 'text' },
  { name: 'weight_per_unit', label: 'Weight per Unit', type: 'number', step: '0.001' },
  { name: 'minimum_stock_level', label: 'Minimum Stock Level', type: 'number', step: '0.01' },
  { name: 'purchase_price', label: 'Purchase Price', type: 'number', step: '0.01', required: true },
  { name: 'selling_price', label: 'Selling Price', type: 'number', step: '0.01', required: true },
  { name: 'mrp', label: 'MRP', type: 'number', step: '0.01', required: true },
  { name: 'gst_percentage', label: 'GST %', type: 'number', step: '0.01', required: true },
  { name: 'description', label: 'Description', type: 'textarea' },
  { name: 'remarks', label: 'Remarks', type: 'textarea' },
  { name: 'is_active', label: 'Active', type: 'checkbox' },
];

const listColumns = [
  { key: 'material_name', header: 'Material Name' },
  { key: 'material_code', header: 'Code' },
  { key: 'unit', header: 'Unit' },
  { key: 'purchase_price', header: 'Purchase Price' },
  { key: 'selling_price', header: 'Selling Price' },
];

export default function Materials() {
  return (
    <MasterDataPage
      title="Materials"
      apiPath="/material/"
      fields={fields}
      listColumns={listColumns}
      searchFields={['material_name', 'material_code']}
    />
  );
}
