
class Proxy < ActiveRecord::Base
	@id
	@ip
	@port
	@country
	@last_contact
	
	validates :ip, :presence => true, :uniqueness => true
	validates :port, :presence => true
	
end