import MasterDataPage from './MasterDataPage';

const SUPPLIER_TYPE_CHOICES = [
  { value: 'MANUFACTURER', label: 'Manufacturer' },
  { value: 'DISTRIBUTOR', label: 'Distributor' },
  { value: 'WHOLESALER', label: 'Wholesaler' },
  { value: 'RETAIL_SUPPLIER', label: 'Retail Supplier' },
  { value: 'LOCAL_TRADER', label: 'Local Trader' },
];

const BALANCE_TYPE_CHOICES = [
  { value: 'CREDIT', label: 'Credit' },
  { value: 'DEBIT', label: 'Debit' },
];

const fields = [
  { name: 'supplier_name', label: 'Supplier Name', type: 'text', required: true },
  { name: 'supplier_code', label: 'Supplier Code', type: 'text', required: true },
  { name: 'supplier_type', label: 'Supplier Type', type: 'select', choices: SUPPLIER_TYPE_CHOICES },
  { name: 'contact_person', label: 'Contact Person', type: 'text' },
  { name: 'mobile_number', label: 'Mobile Number', type: 'text' },
  { name: 'alternate_mobile', label: 'Alternate Mobile', type: 'text' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'gst_number', label: 'GST Number', type: 'text' },
  { name: 'pan_number', label: 'PAN Number', type: 'text' },
  { name: 'address', label: 'Address', type: 'textarea' },
  { name: 'city', label: 'City', type: 'text' },
  { name: 'state', label: 'State', type: 'text' },
  { name: 'pincode', label: 'Pincode', type: 'text' },
  { name: 'opening_balance', label: 'Opening Balance', type: 'number', step: '0.01' },
  { name: 'opening_balance_type', label: 'Balance Type', type: 'select', choices: BALANCE_TYPE_CHOICES },
  { name: 'credit_limit', label: 'Credit Limit', type: 'number', step: '0.01' },
  { name: 'credit_days', label: 'Credit Days', type: 'number' },
  { name: 'bank_name', label: 'Bank Name', type: 'text' },
  { name: 'account_holder_name', label: 'Account Holder Name', type: 'text' },
  { name: 'account_number', label: 'Account Number', type: 'text' },
  { name: 'ifsc_code', label: 'IFSC Code', type: 'text' },
  { name: 'remarks', label: 'Remarks', type: 'textarea' },
  { name: 'is_active', label: 'Active', type: 'checkbox' },
];

const listColumns = [
  { key: 'supplier_name', header: 'Supplier Name' },
  { key: 'supplier_code', header: 'Code' },
  { key: 'supplier_type', header: 'Type' },
  { key: 'mobile_number', header: 'Mobile' },
];

export default function Suppliers() {
  return (
    <MasterDataPage
      title="Suppliers"
      apiPath="/supplier/"
      fields={fields}
      listColumns={listColumns}
      searchFields={['supplier_name', 'supplier_code']}
    />
  );
}
