import MasterDataPage from './MasterDataPage';

const CUSTOMER_TYPE_CHOICES = [
  { value: 'RETAILER', label: 'Retailer' },
  { value: 'DEALER', label: 'Dealer' },
  { value: 'CONTRACTOR', label: 'Contractor' },
  { value: 'BUILDER', label: 'Builder' },
  { value: 'FABRICATOR', label: 'Fabricator' },
  { value: 'OTHER', label: 'Other' },
];

const BALANCE_TYPE_CHOICES = [
  { value: 'DEBIT', label: 'Debit' },
  { value: 'CREDIT', label: 'Credit' },
];

const fields = [
  { name: 'customer_name', label: 'Customer Name', type: 'text', required: true },
  { name: 'customer_code', label: 'Customer Code', type: 'text', required: true },
  { name: 'customer_type', label: 'Customer Type', type: 'select', choices: CUSTOMER_TYPE_CHOICES },
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
  { key: 'customer_name', header: 'Customer Name' },
  { key: 'customer_code', header: 'Code' },
  { key: 'customer_type', header: 'Type' },
  { key: 'mobile_number', header: 'Mobile' },
];

export default function Customers() {
  return (
    <MasterDataPage
      title="Customers"
      apiPath="/customer/"
      fields={fields}
      listColumns={listColumns}
      searchFields={['customer_name', 'customer_code']}
    />
  );
}
