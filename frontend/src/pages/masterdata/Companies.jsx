import MasterDataPage from './MasterDataPage';

const fields = [
  { name: 'company_name', label: 'Company Name', type: 'text', required: true },
  { name: 'company_code', label: 'Company Code', type: 'text', required: true },
  { name: 'gst_number', label: 'GST Number', type: 'text' },
  { name: 'pan_number', label: 'PAN Number', type: 'text' },
  { name: 'contact_person', label: 'Contact Person', type: 'text' },
  { name: 'mobile_number', label: 'Mobile Number', type: 'text' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'address', label: 'Address', type: 'textarea' },
  { name: 'city', label: 'City', type: 'text' },
  { name: 'state', label: 'State', type: 'text' },
  { name: 'pincode', label: 'Pincode', type: 'text' },
  { name: 'is_active', label: 'Active', type: 'checkbox' },
];

const listColumns = [
  { key: 'company_name', header: 'Company Name' },
  { key: 'company_code', header: 'Code' },
  { key: 'city', header: 'City' },
  { key: 'mobile_number', header: 'Mobile' },
];

export default function Companies() {
  return (
    <MasterDataPage
      title="Companies"
      singular="Company"
      apiPath="/company/"
      fields={fields}
      listColumns={listColumns}
      searchFields={['company_name', 'company_code']}
    />
  );
}
